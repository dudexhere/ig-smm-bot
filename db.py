import aiosqlite
import time
import os

# Render persistent disk mount
DB_NAME = os.getenv("DB_NAME", "/var/data/database.db")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            currency TEXT DEFAULT 'INR',
            referred_by INTEGER DEFAULT NULL,
            created_at INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_type TEXT,
            link TEXT,
            quantity INTEGER,
            points_used INTEGER,
            panel_order_id INTEGER,
            status TEXT DEFAULT 'placed',
            created_at INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS topups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_inr INTEGER,
            points_added INTEGER,
            razorpay_order_id TEXT,
            razorpay_payment_id TEXT,
            status TEXT DEFAULT 'created',
            created_at INTEGER
        )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT user_id, username, balance, currency, referred_by FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()

async def add_user(user_id: int, username: str, referred_by=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, username, balance, currency, referred_by, created_at) VALUES(?,?,?,?,?,?)",
            (user_id, username, 0, "INR", referred_by, int(time.time()))
        )
        await db.commit()

async def update_balance(user_id: int, new_balance: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
        await db.commit()

async def change_currency(user_id: int, currency: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET currency=? WHERE user_id=?", (currency, user_id))
        await db.commit()

async def create_order(user_id: int, order_type: str, link: str, qty: int, points_used: int, panel_order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO orders(user_id, order_type, link, quantity, points_used, panel_order_id, status, created_at)
            VALUES(?,?,?,?,?,?,?,?)
        """, (user_id, order_type, link, qty, points_used, panel_order_id, "placed", int(time.time())))
        await db.commit()

async def list_orders(user_id: int, limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
            SELECT id, order_type, quantity, points_used, panel_order_id, status, created_at
            FROM orders WHERE user_id=?
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
        return await cur.fetchall()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cur1 = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cur1.fetchone())[0]
        cur2 = await db.execute("SELECT COUNT(*) FROM orders")
        orders = (await cur2.fetchone())[0]
        return users, orders

async def set_referred_by(user_id: int, ref_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET referred_by=? WHERE user_id=?", (ref_id, user_id))
        await db.commit()

async def create_topup(user_id: int, amount_inr: int, points: int, razorpay_order_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO topups(user_id, amount_inr, points_added, razorpay_order_id, status, created_at)
            VALUES(?,?,?,?,?,?)
        """, (user_id, amount_inr, points, razorpay_order_id, "created", int(time.time())))
        await db.commit()
