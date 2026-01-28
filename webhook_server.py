import hmac
import hashlib
import json
import aiosqlite
from fastapi import FastAPI, Request, HTTPException

from config import RAZORPAY_WEBHOOK_SECRET
from db import DB_NAME, get_user, update_balance

app = FastAPI()

def verify_signature(body: bytes, received_signature: str):
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/razorpay/webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = json.loads(body.decode("utf-8"))
    event = data.get("event")

    if event != "payment.captured":
        return {"status": "ignored", "event": event}

    payment = data["payload"]["payment"]["entity"]
    razorpay_order_id = payment.get("order_id")
    amount_inr = int(payment.get("amount", 0) / 100)

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
            SELECT id, user_id, amount_inr, points_added, status
            FROM topups WHERE razorpay_order_id=?
        """, (razorpay_order_id,))
        row = await cur.fetchone()

        if not row:
            return {"status": "not_found"}

        topup_id, user_id, stored_amt, points_added, status = row

        if status == "paid":
            return {"status": "already_paid"}

        if stored_amt != amount_inr:
            return {"status": "amount_mismatch"}

        await db.execute("""
            UPDATE topups SET status='paid', razorpay_payment_id=?
            WHERE id=?
        """, (payment.get("id"), topup_id))
        await db.commit()

    user = await get_user(user_id)
    if not user:
        return {"status": "user_missing"}

    new_bal = user[2] + points_added
    await update_balance(user_id, new_bal)

    return {"status": "success", "user_id": user_id, "new_balance": new_bal}
