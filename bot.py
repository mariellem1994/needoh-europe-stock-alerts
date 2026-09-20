import os
import urllib.request
import urllib.parse
import json

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATUS_FILE = "stock_status.json"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        print(response.read().decode())


def load_status():

    if not os.path.exists(STATUS_FILE):
        return {}

    try:
        with open(STATUS_FILE, "r") as file:
            return json.load(file)

    except Exception:
        return {}


def save_status(status):

    with open(STATUS_FILE, "w") as file:
        json.dump(status, file, indent=2)


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

        print(f"❌ Error checking page: {e}")

        return None


# ==========================================
# TOYS42HANDS PRODUCT
# ==========================================

product_name = "NeeDoh Jack-Glow Lantern"

product_url = (
    "https://www.toys42hands.nl/en/products/"
    "needoh-jack-glow-latern"
)


# ==========================================
# LOAD PREVIOUS STATUS
# ==========================================

status = load_status()

previous_status = status.get(product_url, False)


# ==========================================
# CHECK CURRENT STOCK
# ==========================================

page = check_stock(product_url)


if page is None:

    print("❌ Could not check Toys42Hands.")

else:

    current_status = (
        '"available":true' in page
        or '"available": true' in page
    )

    print(f"Previous status: {previous_status}")
    print(f"Current status: {current_status}")


    # ======================================
    # PRODUCT JUST CAME INTO STOCK
    # ======================================

    if current_status and not previous_status:

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"🐿️ {product_name}\n"
            f"🛍️ Toys42Hands\n"
            f"🇳🇱 Netherlands\n\n"
            f"🟢 IN STOCK!\n\n"
            f"🔗 {product_url}"
        )

        print("🚨 NEW STOCK! Telegram alert sent.")


    # ======================================
    # PRODUCT STILL IN STOCK
    # ======================================

    elif current_status and previous_status:

        print("🟢 Still in stock — no new alert.")


    # ======================================
    # PRODUCT SOLD OUT
    # ======================================

    elif not current_status and previous_status:

        print("🔴 Product went out of stock.")


    else:

        print("🔴 Still out of stock.")


    # Save current status

    status[product_url] = current_status

    save_status(status)
