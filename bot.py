import asyncio
import re
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import (
    BOT_TOKEN, ADMIN_ID, FORCE_JOIN_LINKS, FORCE_JOIN_USERNAMES,
    SERVICE_IG_LIKES, SERVICE_IG_VIEWS,
    MIN_LIKES, MIN_VIEWS,
    POINTS_PER_LIKE, POINTS_PER_VIEW,
    REFERRAL_BONUS, TOPUP_PACKS
)

from keyboards import main_menu, settings_kb, topup_kb, admin_kb
from db import (
    init_db, add_user, get_user, update_balance, change_currency,
    create_order, list_orders, get_stats, set_referred_by, create_topup
)
from panel_api import panel_add_order, panel_check_status
from razorpay_api import create_razorpay_order

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

INSTAGRAM_POST_REGEX = r"(https?:\/\/)?(www\.)?instagram\.com\/(p|reel)\/[A-Za-z0-9_-]+"

class OrderFlow(StatesGroup):
    link = State()
    qty = State()

class AdminFlow(StatesGroup):
    add_user = State()
    add_amount = State()
    remove_user = State()
    remove_amount = State()
    broadcast = State()

def is_instagram_link(text: str) -> bool:
    return re.search(INSTAGRAM_POST_REGEX, text) is not None

async def is_forced_join_ok(user_id: int) -> bool:
    if not FORCE_JOIN_USERNAMES:
        return True
    for ch in FORCE_JOIN_USERNAMES:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except:
            return False
    return True

def force_join_text() -> str:
    return (
        "🚫 You must join these channels to use the bot:\n\n"
        f"1) {FORCE_JOIN_LINKS[0]}\n"
        f"2) {FORCE_JOIN_LINKS[1]}\n\n"
        "✅ After joining, type /start again."
    )

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    referred_by = None
    if message.text and len(message.text.split()) == 2:
        ref = message.text.split()[1]
        if ref.isdigit():
            referred_by = int(ref)

    await add_user(user_id, username, referred_by=referred_by)

    user = await get_user(user_id)
    if user and user[4] is not None:
        if user[2] == 0 and user[4] != user_id:
            ref_user = await get_user(user[4])
            if ref_user:
                await update_balance(ref_user[0], ref_user[2] + REFERRAL_BONUS)
                await set_referred_by(user_id, user[4])

    if not await is_forced_join_ok(user_id):
        await message.answer(force_join_text())
        return

    await message.answer("✅ Welcome to IG SMM Bot!", reply_markup=main_menu())

@dp.message(F.text == "💰 Balance")
async def balance(message: Message):
    user = await get_user(message.from_user.id)
    await message.answer(f"💰 Balance: {user[2]} points\n💱 Currency: {user[3]}")

@dp.message(F.text == "🎁 Referral")
async def referral(message: Message):
    uid = message.from_user.id
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    await message.answer(
        f"🎁 Referral System\n\n"
        f"Invite link:\n{link}\n\n"
        f"✅ You get {REFERRAL_BONUS} points per referral."
    )

@dp.message(F.text == "⚙️ Settings")
async def settings(message: Message):
    await message.answer("💱 Choose your currency:", reply_markup=settings_kb())

@dp.callback_query(F.data.startswith("setcur:"))
async def set_currency(callback: CallbackQuery):
    cur = callback.data.split(":")[1]
    await change_currency(callback.from_user.id, cur)
    await callback.message.edit_text(f"✅ Currency updated to {cur}")
    await callback.answer()

@dp.message(F.text == "➕ Add Funds")
async def add_funds(message: Message):
    await message.answer("Select top-up amount (INR):", reply_markup=topup_kb())

@dp.callback_query(F.data.startswith("topup:"))
async def topup_create(callback: CallbackQuery):
    amt = int(callback.data.split(":")[1])
    points = TOPUP_PACKS.get(amt, 0)

    receipt = f"topup_{callback.from_user.id}_{int(time.time())}"
    order = create_razorpay_order(amt, receipt)
    razorpay_order_id = order["id"]

    await create_topup(callback.from_user.id, amt, points, razorpay_order_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ I Paid", callback_data=f"paid:{razorpay_order_id}")]
    ])

    await callback.message.edit_text(
        f"✅ Top-up created\n\n"
        f"Amount: ₹{amt}\n"
        f"Points: {points}\n\n"
        f"Razorpay Order ID:\n`{razorpay_order_id}`\n\n"
        f"⚠️ Pay using your Razorpay Checkout.\n"
        f"✅ Webhook will auto add points after payment.\n\n"
        f"Then press ✅ I Paid",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("paid:"))
async def paid_check(callback: CallbackQuery):
    import aiosqlite
    from db import DB_NAME

    order_id = callback.data.split(":")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT status FROM topups WHERE razorpay_order_id=? AND user_id=?",
            (order_id, callback.from_user.id)
        )
        row = await cur.fetchone()

    if not row:
        await callback.answer("❌ Topup not found", show_alert=True)
        return

    if row[0] == "paid":
        user = await get_user(callback.from_user.id)
        await callback.message.edit_text(f"✅ Payment verified!\nNew balance: {user[2]} points")
    else:
        await callback.answer("⏳ Payment not confirmed yet. Wait 10-30 sec.", show_alert=True)

async def start_order(message: Message, state: FSMContext, order_type: str):
    await state.set_state(OrderFlow.link)
    await state.update_data(order_type=order_type)
    await message.answer("📌 Send Instagram Post/Reel Link:")

@dp.message(F.text == "❤️ IG Likes")
async def order_likes(message: Message, state: FSMContext):
    await start_order(message, state, "likes")

@dp.message(F.text == "👁️ IG Views")
async def order_views(message: Message, state: FSMContext):
    await start_order(message, state, "views")

@dp.message(OrderFlow.link)
async def order_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not is_instagram_link(link):
        await message.answer("❌ Invalid link. Send valid Instagram Post/Reel link.")
        return

    data = await state.get_data()
    order_type = data["order_type"]
    await state.update_data(link=link)

    await message.answer(f"✅ Link saved. Now send quantity (Min {MIN_LIKES if order_type=='likes' else MIN_VIEWS})")
    await state.set_state(OrderFlow.qty)

@dp.message(OrderFlow.qty)
async def order_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Quantity must be number.")
        return

    qty = int(message.text)
    data = await state.get_data()
    order_type = data["order_type"]

    if order_type == "likes" and qty < MIN_LIKES:
        await message.answer(f"❌ Minimum likes order is {MIN_LIKES}.")
        return
    if order_type == "views" and qty < MIN_VIEWS:
        await message.answer(f"❌ Minimum views order is {MIN_VIEWS}.")
        return

    user = await get_user(message.from_user.id)
    bal = user[2]

    points_needed = qty * (POINTS_PER_LIKE if order_type == "likes" else POINTS_PER_VIEW)

    if bal < points_needed:
        await message.answer(
            f"❌ Not enough points. Needed: {points_needed}\nYour balance: {bal}\n\n➕ Add funds to continue."
        )
        await state.clear()
        return

    try:
        service_id = SERVICE_IG_LIKES if order_type == "likes" else SERVICE_IG_VIEWS
        panel_id = await panel_add_order(service_id, data["link"], qty)
    except Exception as e:
        await message.answer(f"❌ Failed to place order.\nError: {e}")
        await state.clear()
        return

    await update_balance(message.from_user.id, bal - points_needed)
    await create_order(message.from_user.id, order_type, data["link"], qty, points_needed, panel_id)

    await message.answer(
        f"✅ Order placed!\n\n"
        f"Type: {order_type.upper()}\n"
        f"Quantity: {qty}\n"
        f"Points used: {points_needed}\n"
        f"Panel Order ID: {panel_id}"
    )
    await state.clear()

@dp.message(F.text == "📦 My Orders / Status")
async def my_orders(message: Message):
    orders = await list_orders(message.from_user.id, limit=10)
    if not orders:
        await message.answer("📦 No orders yet.")
        return

    text = "📦 Last 10 Orders:\n\n"
    for o in orders:
        oid, otype, qty, pts, panel_id, status, created_at = o
        text += f"#{oid} | {otype} | qty:{qty} | pts:{pts} | panel:{panel_id} | {status}\n"
    text += "\nTo check status send: /status PANEL_ORDER_ID"
    await message.answer(text)

@dp.message(F.text.startswith("/status"))
async def check_status(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /status PANEL_ORDER_ID")
        return

    panel_id = int(parts[1])
    try:
        st = await panel_check_status(panel_id)
        await message.answer(f"📦 Status:\n`{st}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Failed to check status: {e}")

@dp.message(F.text == "🆘 Support")
async def support(message: Message):
    await message.answer("🆘 Support: Contact admin.")

# Admin
@dp.message(F.text == "/admin")
async def admin_open(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✅ Admin Panel", reply_markup=admin_kb())

@dp.message(F.text == "⬅️ Back")
async def back(message: Message):
    await message.answer("⬅️ Back to menu", reply_markup=main_menu())

@dp.message(F.text == "📊 Stats")
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users, orders = await get_stats()
    await message.answer(f"📊 Stats:\nUsers: {users}\nOrders: {orders}")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
