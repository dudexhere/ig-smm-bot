import requests
from config import PANEL_API_URL, PANEL_API_KEY

def panel_add_order(service: int, link: str, quantity: int) -> int:
    payload = {
        "key": PANEL_API_KEY,
        "action": "add",
        "service": service,
        "link": link,
        "quantity": quantity
    }
    r = requests.post(PANEL_API_URL, data=payload, timeout=40)
    data = r.json()
    if "order" in data:
        return int(data["order"])
    raise Exception(f"Panel error: {data}")

def panel_check_status(order_id: int):
    payload = {
        "key": PANEL_API_KEY,
        "action": "status",
        "order": order_id
    }
    r = requests.post(PANEL_API_URL, data=payload, timeout=40)
    return r.json()

