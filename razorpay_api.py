import razorpay
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_inr: int, receipt: str):
    return client.order.create({
        "amount": amount_inr * 100,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1
    })
