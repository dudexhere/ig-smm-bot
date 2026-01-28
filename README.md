# IG SMM Telegram Bot (Likes + Views) + Razorpay Auto Wallet (Render)

## What you get
- IG Likes + IG Views ordering
- SMM Panel API integration
- Points wallet
- Referral bonus
- Razorpay webhook auto verification + auto points add
- Render deployment ready

## Run local (testing)
pip install -r requirements.txt
python bot.py

## Webhook test local
uvicorn webhook_server:app --host 0.0.0.0 --port 8000

Webhook URL:
http://localhost:8000/razorpay/webhook
