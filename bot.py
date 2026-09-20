import os
import urllib.request
import urllib.parse
import json

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        print(response.read().decode())


def check_toys42hands(url, product_name):
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            page = response.read().decode("utf-8", errors="ignore")

        # Shopify product data
        marker = '"available":'
        available_positions = []

        start = 0
        while True:
            position = page.find(marker, start)

            if position == -1:
                break

            value_start = position + len(marker)
            value = page[value_start:value_start + 10].strip()

            available_positions.append(value.startswith("true"))
            start = value_start

        if any(available_positions):
            send_telegram(
                f"🚨 NEEDOH STOCK ALERT!\n\n"
                f"🐿️ {product_name}\n"
                f"🛍️ Toys42Hands\n"
                f"🇳🇱 Netherlands\n\n"
                f"🟢 IN STOCK!\n\n"
                f"🔗 {url}"
            )

            print(f"🟢 {product_name} appears to be IN STOCK!")

        else:
            print(f"🔴 {product_name} appears to be SOLD OUT.")

    except Exception as e:
        print(f"❌ Error checking {product_name}: {e}")


# ==========================================
# TOYS42HANDS
# ==========================================

product_name = "NeeDoh Jack-Glow Lantern"

product_url = (
    "https://www.toys42hands.nl/en/products/"
    "needoh-jack-glow-latern"
)

check_toys42hands(product_url, product_name)
