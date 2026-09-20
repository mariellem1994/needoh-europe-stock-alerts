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
        with urllib.request.urlopen(url, timeout=15) as response:
            page = response.read().decode("utf-8", errors="ignore")

        return page

    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None


# TEST PRODUCT
product_name = "NeeDoh Mega Niceberg"
test_url = "https://www.intertoys.nl/needoh-mega-niceberg"

page = check_stock(test_url)

if page:
    send_telegram(
        f"🔎 Successfully checked:\n\n"
        f"🐿️ {product_name}\n"
        f"🛍️ Intertoys\n"
        f"🇳🇱 Netherlands\n\n"
        f"✅ Product page downloaded successfully."
    )
else:
    send_telegram(
        "❌ The bot could not download the Intertoys product page."
    )
