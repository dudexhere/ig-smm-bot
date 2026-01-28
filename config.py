import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8583185604"))

# Force Join - invite links shown to user
FORCE_JOIN_LINKS = [
    "https://t.me/+GFIpY5yI7cI4MjJl",
    "https://t.me/+U4FfcewProw2MmY1"
]

# Optional: If you have channel usernames, bot can CHECK membership
FORCE_JOIN_USERNAMES = [
    # "@channel1",
    # "@channel2",
]

# SMM Panel
PANEL_API_URL = os.getenv("PANEL_API_URL", "https://indiansmmpanel.co.in/api")
PANEL_API_KEY = os.getenv("PANEL_API_KEY")

SERVICE_IG_LIKES = 537
SERVICE_IG_VIEWS = 576

MIN_LIKES = 500
MIN_VIEWS = 1000

POINTS_PER_LIKE = 5
POINTS_PER_VIEW = 2

REFERRAL_BONUS = 50

# Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# Currency list (10)
CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SAR", "CAD", "AUD", "SGD", "MYR"]

# Top up packs (INR)
TOPUP_PACKS = {
    10: 4500,
    20: 9500,
    50: 20000,
    100: 45000,
    200: 95000,
    500: 225000,
    1000: 450000,
    5000: 2250000,
    10000: 4500000,
}
TOPUP_MIN = 10
TOPUP_MAX = 10000
