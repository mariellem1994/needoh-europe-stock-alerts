import os
import urllib.request
import urllib.parse

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


def check_stock(url):

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        return page

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


product_name = "NeeDoh Jack-Glow Lantern"

product_url = (
    "https://www.toys42hands.nl/en/products/"
    "needoh-jack-glow-latern"
)

page = check_stock(product_url)

if page:

    if '"available":true' in page or '"available": true' in page:

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"🐿️ {product_name}\n"
            f"🛍️ Toys42Hands\n"
            f"🇳🇱 Netherlands\n\n"
            f"🟢 IN STOCK!\n\n"
            f"🔗 {product_url}"
        )

        print("🟢 Jack-Glow Lantern is IN STOCK!")

    else:

        send_telegram(
            f"🔎 Needoh stock check completed.\n\n"
            f"🐿️ {product_name}\n"
            f"🛍️ Toys42Hands\n\n"
            f"🔴 No stock detected."
        )

else:

    send_telegram(
        "❌ Toys42Hands product page could not be checked."
    )
