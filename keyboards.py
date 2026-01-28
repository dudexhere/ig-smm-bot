from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CURRENCIES, TOPUP_PACKS

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❤️ IG Likes"), KeyboardButton(text="👁️ IG Views")],
            [KeyboardButton(text="💰 Balance"), KeyboardButton(text="➕ Add Funds")],
            [KeyboardButton(text="🎁 Referral"), KeyboardButton(text="📦 My Orders / Status")],
            [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="🆘 Support")]
        ],
        resize_keyboard=True
    )

def settings_kb():
    kb = InlineKeyboardBuilder()
    for cur in CURRENCIES:
        kb.button(text=cur, callback_data=f"setcur:{cur}")
    kb.adjust(5)
    return kb.as_markup()

def topup_kb():
    kb = InlineKeyboardBuilder()
    for amt in sorted(TOPUP_PACKS.keys()):
        kb.button(text=f"₹{amt}", callback_data=f"topup:{amt}")
    kb.adjust(3)
    return kb.as_markup()

def admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add Points"), KeyboardButton(text="➖ Remove Points")],
            [KeyboardButton(text="📊 Stats"), KeyboardButton(text="📢 Broadcast")],
            [KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True
    )
