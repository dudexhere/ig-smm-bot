import aiohttp
from config import PANEL_API_URL, PANEL_API_KEY

async def panel_add_order(service: int, link: str, quantity: int) -> int:
    payload = {
        "key": PANEL_API_KEY,
        "action": "add",
        "service": service,
        "link": link,
        "quantity": quantity
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(PANEL_API_URL, data=payload, timeout=40) as resp:
            data = await resp.json(content_type=None)

    if "order" in data:
        return int(data["order"])
    raise Exception(f"Panel error: {data}")

async def panel_check_status(order_id: int):
    payload = {"key": PANEL_API_KEY, "action": "status", "order": order_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(PANEL_API_URL, data=payload, timeout=40) as resp:
            return await resp.json(content_type=None)
