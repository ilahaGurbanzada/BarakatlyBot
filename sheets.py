"""
Google Sheets Integration — via Apps Script Webhook
====================================================

Sends orders to a Google Apps Script web app, which writes to your sheet.
No Cloud Console, no service account, no credentials.json file.

How it works:
  bot → HTTPS POST → Apps Script URL → your Google Sheet

The URL goes in your .env file as SHEETS_WEBHOOK_URL.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")


def save_order_to_sheet(order: dict) -> None:
    """Send an order to Google Sheets via the Apps Script webhook."""
    if not SHEETS_WEBHOOK_URL:
        raise ValueError("SHEETS_WEBHOOK_URL not set in .env file")

    # Format items as readable text: "Yumurta (30 ədəd); Süd (2 L)"
    from menu import PRODUCTS
    item_lines = []
    for product_id, qty in order["items"].items():
        if product_id in PRODUCTS:
            p = PRODUCTS[product_id]
            item_lines.append(f"{p['name_az']} ({qty:g} {p['unit_label_az']})")
    items_str = "; ".join(item_lines)

    payload = {
        "order_id": order["order_id"],
        "timestamp": order["timestamp"],
        "customer_name": order["customer_name"],
        "customer_phone": order["customer_phone"],
        "telegram_username": order.get("telegram_username", ""),
        "delivery_date": order["delivery_date"],
        "items_str": items_str,
        "total_azn": round(order["total_azn"], 2),
        "maps_link": order["maps_link"],
        "location_lat": order["location_lat"],
        "location_lng": order["location_lng"],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SHEETS_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response_text = response.read().decode("utf-8")
            try:
                result = json.loads(response_text)
                if result.get("status") != "success":
                    logger.warning(f"Webhook returned non-success: {result}")
                    raise Exception(f"Webhook error: {result}")
            except json.JSONDecodeError:
                logger.warning(f"Webhook returned non-JSON: {response_text[:200]}")
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error from webhook: {e.code} {e.reason}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"Network error reaching webhook: {e.reason}")
        raise


if __name__ == "__main__":
    # Quick test: send a fake order to verify the webhook works
    print("Testing webhook with a fake order...")
    test_order = {
        "order_id": "TEST-CONNECTION",
        "timestamp": "2026-05-08T12:00:00",
        "customer_name": "Test Customer",
        "customer_phone": "+994000000000",
        "telegram_username": "testuser",
        "delivery_date": "10.05.2026",
        "items": {"yumurta": 30},
        "total_azn": 12.00,
        "maps_link": "https://maps.google.com/?q=40.4,49.9",
        "location_lat": 40.4093,
        "location_lng": 49.8671,
    }
    try:
        save_order_to_sheet(test_order)
        print("✅ Success! Check your Google Sheet — a TEST-CONNECTION row should appear.")
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("   Check your SHEETS_WEBHOOK_URL in .env")
