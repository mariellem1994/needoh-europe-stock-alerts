import os
import urllib.request
import urllib.parse
import re
from html import unescape

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


def get_page(url):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")

    except Exception as e:
        print(f"❌ Could not open {url}: {e}")
        return None


def check_toys42hands_collection():

    collection_url = (
        "https://www.toys42hands.nl/en/collections/needoh"
    )

    page = get_page(collection_url)

    if not page:
        send_telegram(
            "❌ Toys42Hands could not be checked."
        )
        return

    print("✅ Toys42Hands collection downloaded.")

    # Find product links in the collection
    pattern = r'href="(/en/products/[^"]+)"'
    links = re.findall(pattern, page)

    # Remove duplicates
    links = list(dict.fromkeys(links))

    print(f"🔎 Found {len(links)} product links.")

    found_stock = False

    for link in links:

        product_url = "https://www.toys42hands.nl" + unescape(link)

        product_page = get_page(product_url)

        if not product_page:
            continue

        # Shopify product pages contain "available":true
        if '"available":true' in product_page:

            # Try to find the product title
            title_match = re.search(
                r'<title[^>]*>(.*?)</title>',
                product_page,
                re.IGNORECASE | re.DOTALL
            )

            if title_match:
                product_name = re.sub(
                    r'\s+',
                    ' ',
                    unescape(title_match.group(1))
                ).strip()

                # Remove shop name from title if present
                product_name = product_name.split("–")[0].strip()
            else:
                product_name = "NeeDoh"

            send_telegram(
                f"🚨 NEEDOH STOCK ALERT!\n\n"
                f"➡️ {product_name}\n"
                f"🛍️ Toys42Hands\n"
                f"🇳🇱 Netherlands\n\n"
                f"🟢 IN STOCK!\n\n"
                f"🔗 {product_url}"
            )

            print(f"🟢 IN STOCK: {product_name}")

            found_stock = True

    if not found_stock:
        print("🔴 No in-stock Needohs found.")


# ==========================================
# RUN TOYS42HANDS CHECK
# ==========================================

check_toys42hands_collection()
