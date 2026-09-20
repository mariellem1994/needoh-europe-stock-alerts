import os
import urllib.request
import urllib.parse
import json
from datetime import datetime
from zoneinfo import ZoneInfo


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


RADAR_URL = "https://mariellem1994.github.io/needoh-europe-stock-alerts/"


def send_telegram(message, button_url=None):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    if button_url:

        data["reply_markup"] = json.dumps({
            "inline_keyboard": [[
                {
                    "text": "📡 OPEN LIVE RADAR",
                    "url": button_url
                }
            ]]
        })

    data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        return response.read()


def load_previous_radar():

    try:

        with open(
            "radar.json",
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        print("ℹ️ No previous radar data found.")

        return None


def get_previous_status(
    previous_radar,
    shop_name,
    product_name
):

    if not previous_radar:
        return None

    for shop in previous_radar.get(
        "shops",
        []
    ):

        if shop.get("name") != shop_name:
            continue

        for product in shop.get(
            "products",
            []
        ):

            if product.get("name") == product_name:

                return product.get("status")

    return None


def check_lobbes_stock():

    url = "https://www.lobbes.nl/merken/needoh"

    try:

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
                "Referer": "https://www.lobbes.nl/"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=20
        ) as response:

            html = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        html_lower = html.lower()

        results = []

        product_positions = []

        for product in lobbes_products:

            product_path = urllib.parse.urlparse(
                product["url"]
            ).path.lower()

            position = html_lower.find(
                product_path
            )

            product_positions.append({
                "product": product,
                "position": position
            })


        product_positions.sort(
            key=lambda item:
                item["position"]
                if item["position"] != -1
                else 999999999
        )


        for i, item in enumerate(
            product_positions
        ):

            product = item["product"]
            start = item["position"]


            if start == -1:

                results.append({
                    "name": product["name"],
                    "url": product["url"],
                    "status": "error"
                })

                continue


            if i + 1 < len(
                product_positions
            ):

                next_position = (
                    product_positions[
                        i + 1
                    ]["position"]
                )

                if next_position != -1:

                    section = html_lower[
                        start:next_position
                    ]

                else:

                    section = html_lower[
                        start:
                    ]

            else:

                section = html_lower[
                    start:
                ]


            if (
                "uitverkocht" in section
                or
                "dit artikel is nu niet leverbaar"
                in section
                or
                "momenteel niet leverbaar"
                in section
            ):

                status = "out_of_stock"

            else:

                status = "in_stock"


            results.append({
                "name": product["name"],
                "url": product["url"],
                "status": status
            })


        return results


    except Exception as e:

        print(
            f"⚠️ Lobbes error: {e}"
        )

        return []


def check_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        return page


    except Exception as e:

        print(
            f"❌ Error checking {url}: {e}"
        )

        return None

def check_intertoys_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()


        # Intertoys explicitly says these products
        # are only available in physical stores.
        if (
            "alleen in de winkel te koop"
            in page_lower
        ):

            return "out_of_stock"


        # We ONLY count the product as online stock
        # when Intertoys offers home delivery.
        if (
            "thuisbezorgen"
            in page_lower
        ):

            return "in_stock"


        # Store stock / Click & Collect alone
        # does NOT count as online stock.
        return "out_of_stock"


    except Exception as e:

        print(
            f"⚠️ Intertoys error: {e}"
        )

        return "error"

def check_smyths_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()


        # Smyths distinguishes online/home delivery
        # from local store availability.
        #
        # We only want genuine online purchasing.
        # Store-only availability must NOT trigger an alert.

        if (
            "home delivery"
            in page_lower
            or
            "thuisbezorgen"
            in page_lower
        ):

            return "in_stock"


        return "out_of_stock"


    except Exception as e:

        print(
            f"⚠️ Smyths error: {e}"
        )

        return "error"

def check_dreamland_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()

        if "tijdelijk uitverkocht" in page_lower:
            return "out_of_stock"

        if "niet leverbaar" in page_lower:
            return "out_of_stock"

        if "levering aan huis" in page_lower:
            return "in_stock"

        return "out_of_stock"

    except Exception as e:

        print(f"⚠️ DreamLand error: {e}")

        return "error"

def check_houten_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()

        # Shopify usually exposes availability in the product page
        if (
            '"available":true' in page_lower
            or
            '"available": true' in page_lower
        ):
            return "in_stock"

        if (
            "uitverkocht" in page_lower
            or
            "sold out" in page_lower
        ):
            return "out_of_stock"

        return "out_of_stock"

    except Exception as e:

        print(f"⚠️ Houten Onderwijsmateriaal error: {e}")

        return "error"

def check_drukke_mamas_collection():

    try:

        request = urllib.request.Request(
            drukke_mamas_collection_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        return page

    except Exception as e:

        print(f"⚠️ Drukke Mama's error: {e}")

        return None

def get_drukke_mamas_needoh_products(page):

    if not page:
        return []

    import re
    from html import unescape

    products = []

    matches = re.findall(
        r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        page,
        re.IGNORECASE | re.DOTALL
    )

    for url, content in matches:

        text = re.sub("<.*?>", " ", content)
        text = unescape(text)
        text = " ".join(text.split())

        combined_text = (text + " " + url).lower()

        if "needoh" not in combined_text:
            continue

        if "section-template" in text.lower():
            continue

        if "filter-container" in text.lower():
            continue

        if "air_reviews" in text.lower():
            continue

        if "javascript" in text.lower():
            continue

        if "stylesheet" in text.lower():
            continue

        if text.lower().strip() == "needoh":
            continue

        if "wis alle filters" in text.lower():
            continue

        if len(text) < 5:
            continue

        if len(text) > 150:
            continue

        if url.startswith("/"):
            full_url = "https://drukkemamas.be" + url

        elif url.startswith("http"):
            full_url = url

        else:
            continue

        products.append({
            "name": text,
            "url": full_url
        })

    unique_products = []

    seen_urls = set()

    for product in products:

        if product["url"] not in seen_urls:

            seen_urls.add(product["url"])
            unique_products.append(product)

    return unique_products

def get_spadt_needoh_products(page):

    if not page:
        return []

    import re
    from html import unescape

    products = []

    matches = re.findall(
        r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        page,
        re.IGNORECASE | re.DOTALL
    )

    for url, content in matches:

        text = re.sub("<.*?>", " ", content)
        text = unescape(text)
        text = " ".join(text.split())

        combined_text = (text + " " + url).lower()

        if (
            "needoh" not in combined_text
            and "squishmas" not in combined_text
        ):
            continue

        if url.rstrip("/") in (
            "/merken/schylling",
            "/merken/schylling/"
        ):
            continue

        if text.lower().strip() in (
            "needoh",
            "schylling",
            "needoh schylling"
        ):
            continue

        if url.startswith("/"):
            full_url = "https://spadt.be" + url

        elif url.startswith("http"):
            full_url = url

        else:
            continue

        products.append({
            "name": text,
            "url": full_url
        })

    unique_products = []

    seen_urls = set()

    for product in products:

        if product["url"] not in seen_urls:

            seen_urls.add(product["url"])
            unique_products.append(product)

    return unique_products
    

def check_spadt_collection():

    try:

        request = urllib.request.Request(
            spadt_collection_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        return page

    except Exception as e:

        print(f"⚠️ Spadt error: {e}")

        return None

    unique_products = []

    seen_urls = set()

    for product in products:

        if product["url"] not in seen_urls:

            seen_urls.add(product["url"])
            unique_products.append(product)

    return unique_products

def check_spadt_product_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()

        if (
            "uitverkocht" in page_lower
            or
            "tijdelijk uitverkocht" in page_lower
            or
            "niet beschikbaar" in page_lower
            or
            "out of stock" in page_lower
        ):
            return "out_of_stock"

        if (
            "in winkelwagen" in page_lower
            or
            "toevoegen aan winkelwagen" in page_lower
            or
            "add to cart" in page_lower
        ):
            return "in_stock"

        return "out_of_stock"

    except Exception as e:

        print(f"⚠️ Spadt product error: {e}")

        return "error"

def check_mamiee_collection():

    try:

        request = urllib.request.Request(
            mamiee_collection_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        return page

    except Exception as e:

        print(f"⚠️ Mamiee error: {e}")

        return None

def check_mamiee_product_stock(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        page_lower = page.lower()

        if (
            "vyprodáno" in page_lower
            or
            "není skladem" in page_lower
            or
            "out of stock" in page_lower
        ):
            return "out_of_stock"

        if (
            "do košíku" in page_lower
            or
            "koupit" in page_lower
            or
            "přidat do košíku" in page_lower
        ):
            return "in_stock"

        return "out_of_stock"

    except Exception as e:

        print(f"⚠️ Mamiee product error: {e}")

        return "error"

def get_mamiee_needoh_products(page):

    if not page:
        return []

    import re
    from html import unescape

    products = []

    matches = re.findall(
        r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        page,
        re.IGNORECASE | re.DOTALL
    )

    for url, content in matches:

        text = re.sub("<.*?>", " ", content)
        text = unescape(text)
        text = " ".join(text.split())

        combined_text = (text + " " + url).lower()

        if "needoh" not in combined_text:
            continue

        if (
            "opět v nabídce" in text.lower()
            or
            "koupit radost" in text.lower()
            or
            "popis:" in text.lower()
            or
            "výrobce:" in text.lower()
        ):
            continue

        if text.lower().strip() in (
            "needoh",
            "search",
            "hledat"
        ):
            continue

        if len(text) < 5:
            continue

        if len(text) > 150:
            continue

        if url.startswith("/"):
            full_url = "https://www.mamiee.cz" + url

        elif url.startswith("http"):
            full_url = url

        else:
            continue

        products.append({
            "name": text,
            "url": full_url
        })

    unique_products = []

    seen_urls = set()

    for product in products:

        if product["url"] not in seen_urls:

            seen_urls.add(product["url"])
            unique_products.append(product)

    return unique_products

products = [

    {
        "name": "Squisher the Reindoh",
        "url": "https://www.toys42hands.nl/en/products/squisher-the-reindoh"
    },
    {
        "name": "Teenie Jack-Glow Lantern",
        "url": "https://www.toys42hands.nl/en/products/needoh-teenie-jack-glow-latern"
    },
    {
        "name": "Knittens",
        "url": "https://www.toys42hands.nl/en/products/knittens"
    },
    {
        "name": "Teenie Singles Needoh",
        "url": "https://www.toys42hands.nl/en/products/teenie-singles-needoh"
    },
    {
        "name": "NeeDoh Nice Cube",
        "url": "https://www.toys42hands.nl/en/products/needoh-nice-cube"
    },
    {
        "name": "NeeDoh Squishmas Fidget Advent Calendar",
        "url": "https://www.toys42hands.nl/en/products/needoh-sqishmas-fidget-adventskalender"
    },
    {
        "name": "NeeDoh Ice Baby Teenie 6-pack",
        "url": "https://www.toys42hands.nl/en/products/needoh-ice-baby-teenie-6-stuks"
    },
    {
        "name": "NeeDoh Jelly Squish",
        "url": "https://www.toys42hands.nl/en/products/needoh-jelly-squish"
    },
    {
        "name": "Teenie NeeDoh Fuzz Balls 3-pack",
        "url": "https://www.toys42hands.nl/en/products/teenie-needoh-fuzz-balls-3-stuks"
    },
    {
        "name": "NeeDoh Nice Berg Swirl",
        "url": "https://www.toys42hands.nl/en/products/needoh-nice-berg-swirl"
    },
    {
        "name": "NeeDoh Wonder Wave Fuzz",
        "url": "https://www.toys42hands.nl/en/products/needoh-wonder-wave-fuzz"
    },
    {
        "name": "NeeDoh Mello Mallo",
        "url": "https://www.toys42hands.nl/en/products/needoh-mello-mallo"
    },
    {
        "name": "NeeDoh Snow Ball Crunch",
        "url": "https://www.toys42hands.nl/en/products/schylling-snow-ball-crunch-en"
    },
    {
        "name": "NeeDoh Super Fuzz",
        "url": "https://www.toys42hands.nl/en/products/needoh-super-fuzz-antistressball"
    },
    {
        "name": "Teenie Nice Ice Baby NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/teenie-nice-ice-baby-needoh"
    },
    {
        "name": "NeeDoh Cool Cat",
        "url": "https://www.toys42hands.nl/en/products/needoh-cool-cat"
    },
    {
        "name": "Super NeeDoh Ripples",
        "url": "https://www.toys42hands.nl/en/products/super-needoh-ripples"
    },
    {
        "name": "NeeDoh Dream Drop",
        "url": "https://www.toys42hands.nl/en/products/needoh-dream-drop"
    },
    {
        "name": "NeeDoh Gumdrop",
        "url": "https://www.toys42hands.nl/en/products/needoh-gumdrop"
    },
    {
        "name": "NeeDoh Swirl Teenie 6-pack",
        "url": "https://www.toys42hands.nl/en/products/needoh-swirl-teenie-6-stuks"
    },
    {
        "name": "NeeDoh Nice Cube Glow",
        "url": "https://www.toys42hands.nl/en/products/needoh-nice-cube-glow"
    },
    {
        "name": "NeeDoh Sploot Splat",
        "url": "https://www.toys42hands.nl/en/products/needoh-sploot-splat"
    },
    {
        "name": "Atomic NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/atomic-needoh-antistressbal"
    },
    {
        "name": "Color Changing NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/color-changing-needoh"
    },
    {
        "name": "Swirl NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/schylling-swirl-needoh-en"
    },
    {
        "name": "NeeDoh Booper",
        "url": "https://www.toys42hands.nl/en/products/schylling-needoh-booper-en"
    },
    {
        "name": "Teenie NeeDoh Fuzz Ball",
        "url": "https://www.toys42hands.nl/en/products/teenie-needoh-fuzz-bal"
    },
    {
        "name": "NeeDoh Nice Berg",
        "url": "https://www.toys42hands.nl/en/products/needoh-niceberg"
    },
    {
        "name": "Teenie NeeDoh 3-pack",
        "url": "https://www.toys42hands.nl/en/products/needoh-teenie-3-stuks"
    },
    {
        "name": "NeeDoh Groovy Glob",
        "url": "https://www.toys42hands.nl/en/products/needoh-groovy-glob"
    },
    {
        "name": "NeeDoh Funky Pup",
        "url": "https://www.toys42hands.nl/en/products/schylling-funky-pup-kneading-ball"
    },
    {
        "name": "Shaggy NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/shaggy-needoh"
    },
    {
        "name": "NeeDoh Glitter Glow Nice Cube",
        "url": "https://www.toys42hands.nl/en/products/needoh-glitter-glow-nice-cube"
    },
    {
        "name": "Nice Cube Swirl NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/nice-cube-swirl-needoh"
    },
    {
        "name": "Lava Slime",
        "url": "https://www.toys42hands.nl/en/products/lava-slime"
    },
    {
        "name": "Teenie Cool Cat NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/teenie-cool-cat-needoh"
    },
    {
        "name": "NeeDoh Flower Power Fuzz",
        "url": "https://www.toys42hands.nl/en/products/needoh-flower-power-fuzz"
    },
    {
        "name": "Teenie Funky Pup NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/teenie-funky-pop-needoh"
    },
    {
        "name": "Mac N Squeeze NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/schylling-mac-n-squeeze-needoh-en"
    },
    {
        "name": "Rainbow NeeDoh",
        "url": "https://www.toys42hands.nl/en/products/regenboog-needoh"
    },
    {
        "name": "Ramen Noodlies",
        "url": "https://www.toys42hands.nl/en/products/schylling-ramen-noodlies-fidget-en"
    },
    {
        "name": "NeeDoh Jack-Glow Lantern",
        "url": "https://www.toys42hands.nl/en/products/needoh-jack-glow-latern"
    }

]

intertoys_products = [

    {
        "name": "NeeDoh Mega Niceberg",
        "url": "https://www.intertoys.nl/needoh-mega-niceberg"
    },

    {
        "name": "NeeDoh Nice Cube Swirl",
        "url": "https://www.intertoys.nl/needoh-nice-cube-swirl"
    },

    {
        "name": "NeeDoh Dream Drop",
        "url": "https://www.intertoys.nl/needoh-dream-drop"
    },

    {
        "name": "NeeDoh Teenie NeeDoh 3-pack",
        "url": "https://www.intertoys.nl/needoh-teenie-needoh-3-pack"
    },

    {
        "name": "NeeDoh Sugar Skull Cats",
        "url": "https://www.intertoys.nl/needoh-sugar-skull-cats"
    },

    {
        "name": "NeeDoh glow in the dark",
        "url": "https://www.intertoys.nl/needoh-glow-in-the-dark"
    },

    {
        "name": "NeeDoh Hot Shots voetbal",
        "url": "https://www.intertoys.nl/needoh-hot-shots-voetbal"
    },

    {
        "name": "NeeDoh Teenie Fab Four multipack",
        "url": "https://www.intertoys.nl/needoh-teenie-fab-four-multipack-stressballen"
    },

    {
        "name": "NeeDoh coole kat",
        "url": "https://www.intertoys.nl/needoh-coole-kat"
    },

    {
        "name": "NeeDoh Color Change",
        "url": "https://www.intertoys.nl/needoh-color-change"
    },

    {
        "name": "NeeDoh Nice Cube",
        "url": "https://www.intertoys.nl/needoh-nice-cube"
    },

    {
        "name": "Needoh Classic Needoh stressbal",
        "url": "https://www.intertoys.nl/needoh-classic-needoh-stressbal"
    }

]

smyths_products = [

    {
        "name": "NeeDoh Nice Cube",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-nice-cube-stressbal-assorti/p/246112"
    },

    {
        "name": "NeeDoh Snow Ball Crunch",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-stressbal-snow-ball-crunch/p/246113"
    },

    {
        "name": "NeeDoh Mello Mallo",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-stressball-mello-mallo-met-kleureffect-assorti/p/255806"
    },

    {
        "name": "NeeDoh Wonder Waves",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-stressbal-fuzz-bal-wonder-waves-assorti/p/255807"
    },

    {
        "name": "NeeDoh Cool Cats",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-cool-cats-stressbal-assorti/p/255826"
    },

    {
        "name": "NeeDoh Advent Calendar",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/adventskalender/needoh-adventskalender/p/258225"
    },

    {
        "name": "NeeDoh Color Changer",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-color-changer-stressbal-met-kleurverandering-assorti/p/258939"
    },

    {
        "name": "NeeDoh Nice Cube Glow",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-nice-cube-fidget-speelgoed-assorti/p/257976"
    },

    {
        "name": "NeeDoh Nice Cube Glitter & Glow",
        "url": "https://www.smythstoys.com/nl/nl-nl/speelgoed/zakgeld/needoh-nice-cube-stressbal-glitter-en-glow-assorti/p/259966"
    }

]

dreamland_products = [
    {
        "name": "NeeDoh Niceberg",
        "url": "https://www.dreamland.nl/producten/needoh-niceberg-needoh/01857931"
    },
    {
        "name": "NeeDoh Nice Berg Swirl",
        "url": "https://www.dreamland.nl/producten/needoh-nice-berg-swirl/02356846"
    },
    {
        "name": "NeeDoh Nice Berg Glitter & Glow",
        "url": "https://www.dreamland.nl/producten/needoh-nice-berg-glitter-glow/02356860"
    }
]

houten_products = [
    {
        "name": "Dream Drop NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/dream-drop-needoh"
    },
    {
        "name": "Verkleurende NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/verkleurende-needoh"
    },
    {
        "name": "Gumdrop NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/gumdrop-needoh"
    },
    {
        "name": "Nice Cube NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/nice-cube-needoh"
    },
    {
        "name": "Donut NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/donut-needoh"
    },
    {
        "name": "Marbleez NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/marbleez-needoh"
    },
    {
        "name": "Sploot Splat NeeDoh",
        "url": "https://houtenonderwijsmateriaal.be/products/sploot-splat-needoh"
    }
]

drukke_mamas_collection_url = "https://drukkemamas.be/collections/needoh"

spadt_collection_url = "https://spadt.be/merken/schylling/"

mamiee_collection_url = "https://www.mamiee.cz/search?phrase=Needoh"

lobbes_products = [

    {
        "name": "Niceberg",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650684-needoh-niceberg-needoh"
    },
    {
        "name": "Gumdrop",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650670-needoh-gumdrop-needoh"
    },
    {
        "name": "Cool Cats",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650672-needoh-cool-cats-kat"
    },
    {
        "name": "Color Change",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650673-needoh-color-change"
    },
    {
        "name": "Nice Cube Glow",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650686-needoh-nice-cube-glow-needoh"
    },
    {
        "name": "Nice Cube",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650669-needoh-nice-cube-sensorisch-stressspeeltje-met-goo-vulling"
    },
    {
        "name": "Teenie Glob",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650674-needoh-teenie-glob-kleur-3-pack"
    },
    {
        "name": "Dream Pop",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650675-needoh-dream-pop-needoh"
    },
    {
        "name": "Wonder Waves",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650687-needoh-fuzz-ball-wonder-waves-needoh"
    },
    {
        "name": "Mello Mallo",
        "url": "https://www.lobbes.nl/speelgoed/uitdeelcadeautjes/fidget-toys/detail/4650689-needoh-mello-mallo-needoh"
    }

]


previous_radar = load_previous_radar()

intertoys_results = []

for product in intertoys_products:

    print(
        f"Checking Intertoys: {product['name']}"
    )

    current_status = check_intertoys_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "Intertoys",
        product["name"]
    )


    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(

            f"🚨 NEEDOH STOCK ALERT!\n\n"

            f"➡️ {product['name']}\n"

            f"🛍️ Intertoys\n"

            f"🇳🇱 Netherlands\n\n"

            f"🟢 IN STOCK ONLINE!\n\n"

            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW INTERTOYS STOCK: {product['name']}"
        )


    intertoys_results.append({

        "name": product["name"],

        "url": product["url"],

        "status": current_status

    })
    smyths_results = []

for product in smyths_products:

    print(
        f"Checking Smyths: {product['name']}"
    )

    current_status = check_smyths_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "Smyths",
        product["name"]
    )


    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(

            f"🚨 NEEDOH STOCK ALERT!\n\n"

            f"➡️ {product['name']}\n"

            f"🛍️ Smyths Toys\n"

            f"🇳🇱 Netherlands\n\n"

            f"🟢 IN STOCK ONLINE!\n\n"

            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW SMYTHS STOCK: {product['name']}"
        )

    else:

        if current_status == "in_stock":

            print(
                f"🟢 In stock online: {product['name']} "
                f"(no new alert)"
            )

        elif current_status == "out_of_stock":

            print(
                f"🔴 Out of stock online: {product['name']}"
            )

        else:

            print(
                f"⚠️ Could not check: {product['name']}"
            )


    smyths_results.append({

        "name": product["name"],

        "url": product["url"],

        "status": current_status

    })

dreamland_results = []

for product in dreamland_products:

    print(
        f"Checking DreamLand: {product['name']}"
    )

    current_status = check_dreamland_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "DreamLand",
        product["name"]
    )

    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ DreamLand\n"
            f"🇳🇱 Netherlands\n\n"
            f"🟢 IN STOCK ONLINE!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW DREAMLAND STOCK: {product['name']}"
        )

    else:

        if current_status == "in_stock":

            print(
                f"🟢 In stock online: {product['name']} "
                f"(no new alert)"
            )

        elif current_status == "out_of_stock":

            print(
                f"🔴 Out of stock online: {product['name']}"
            )

        else:

            print(
                f"⚠️ Could not check: {product['name']}"
            )

    dreamland_results.append({
        "name": product["name"],
        "url": product["url"],
        "status": current_status
    })

drukke_mamas_results = []

drukke_mamas_page = check_drukke_mamas_collection()

drukke_mamas_products = get_drukke_mamas_needoh_products(
    drukke_mamas_page
)

print(
    f"Found {len(drukke_mamas_products)} NeeDoh products "
    f"at Drukke Mama's"
)

for product in drukke_mamas_products:

    print(
        f"Drukke Mama's: {product['name']}"
    )

    drukke_mamas_results.append({
        "name": product["name"],
        "url": product["url"],
        "status": "unknown"
    })

for product in drukke_mamas_products:

    previous_status = get_previous_status(
        previous_radar,
        "Drukke Mama's",
        product["name"]
    )

if (
    previous_status is None
    and any(
        shop["name"] == "Drukke Mama's"
        for shop in previous_radar.get("shops", [])
    )
):

        send_telegram(
            f"🚨 NEW NEEDOH FOUND!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Drukke Mama's\n"
            f"🇧🇪 Belgium\n\n"
            f"🆕 NEW PRODUCT FOUND!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW DRUKKE MAMA'S NEEDOH: "
            f"{product['name']}"
        )

spadt_results = []

spadt_page = check_spadt_collection()

spadt_products = get_spadt_needoh_products(
    spadt_page
)

print(
    f"Found {len(spadt_products)} NeeDoh products "
    f"at Spadt"
)

for product in spadt_products:

    print(
        f"Checking Spadt: {product['name']}"
    )

    current_status = check_spadt_product_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "Spadt",
        product["name"]
    )

    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Spadt\n"
            f"🇧🇪 Belgium\n\n"
            f"🟢 BACK IN STOCK ONLINE!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW SPADT STOCK: {product['name']}"
        )

    spadt_results.append({
        "name": product["name"],
        "url": product["url"],
        "status": current_status
    })

for product in spadt_products:

    previous_status = get_previous_status(
        previous_radar,
        "Spadt",
        product["name"]
    )

    if (
        previous_status is None
        and any(
            shop["name"] == "Spadt"
            for shop in previous_radar.get("shops", [])
        )
    ):

        send_telegram(
            f"🚨 NEW NEEDOH FOUND!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Spadt\n"
            f"🇧🇪 Belgium\n\n"
            f"🆕 NEW PRODUCT FOUND!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW SPADT NEEDOH: "
            f"{product['name']}"
        )


mamiee_results = []

mamiee_page = check_mamiee_collection()

mamiee_products = get_mamiee_needoh_products(
    mamiee_page
)

print(
    f"Found {len(mamiee_products)} NeeDoh products "
    f"at Mamiee"
)

for product in mamiee_products:

    print(
        f"Checking Mamiee: {product['name']}"
    )

    current_status = check_mamiee_product_stock(
        product["url"]
    )

    if current_status == "in_stock":
        print(
            f"🟢 In stock: {product['name']}"
        )

    elif current_status == "out_of_stock":
        print(
            f"🔴 Out of stock: {product['name']}"
        )

    else:
        print(
            f"⚠️ Could not check: {product['name']}"
        )

    previous_status = get_previous_status(
        previous_radar,
        "Mamiee",
        product["name"]
    )

    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Mamiee\n"
            f"🇨🇿 Czech Republic\n\n"
            f"🟢 BACK IN STOCK ONLINE!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW MAMIEE STOCK: "
            f"{product['name']}"
        )

    mamiee_results.append({
        "name": product["name"],
        "url": product["url"],
        "status": current_status
    })
    
houten_results = []

for product in houten_products:

    print(
        f"Checking Houten Onderwijsmateriaal: {product['name']}"
    )

    current_status = check_houten_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "Houten Onderwijsmateriaal",
        product["name"]
    )

    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Houten Onderwijsmateriaal\n"
            f"🇧🇪 Belgium\n\n"
            f"🟢 IN STOCK ONLINE!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW HOUTEN STOCK: {product['name']}"
        )

    else:

        if current_status == "in_stock":

            print(
                f"🟢 In stock online: {product['name']} "
                f"(no new alert)"
            )

        elif current_status == "out_of_stock":

            print(
                f"🔴 Out of stock online: {product['name']}"
            )

        else:

            print(
                f"⚠️ Could not check: {product['name']}"
            )

    houten_results.append({
        "name": product["name"],
        "url": product["url"],
        "status": current_status
    })
    
print(
    f"🔎 Checking {len(products)} Needoh products..."
)


statuses = []


for product in products:

    print(
        f"Checking: {product['name']}"
    )

    page = check_stock(
        product["url"]
    )


    if page:

        if (
            '"available":true'
            in page
            or
            '"available": true'
            in page
        ):

            current_status = "in_stock"

            statuses.append(
                f"🟢 {product['name']}"
            )

            previous_status = get_previous_status(
                previous_radar,
                "Toys42Hands",
                product["name"]
            )


            if (
                previous_status == "out_of_stock"
            ):

                send_telegram(

                    f"🚨 NEEDOH STOCK ALERT!\n\n"

                    f"➡️ {product['name']}\n"

                    f"🛍️ Toys42Hands\n"

                    f"🇳🇱 Netherlands\n\n"

                    f"🟢 IN STOCK!\n\n"

                    f"🔗 {product['url']}"
                )

                print(
                    f"🚨 NEW STOCK: {product['name']}"
                )

            else:

                print(
                    f"🟢 In stock: {product['name']} "
                    f"(no new alert)"
                )


        else:

            current_status = "out_of_stock"

            statuses.append(
                f"🔴 {product['name']}"
            )

            print(
                f"🔴 Out of stock: {product['name']}"
            )


    else:

        current_status = "error"

        statuses.append(
            f"⚠️ {product['name']} — could not check"
        )

        print(
            f"⚠️ Could not check: {product['name']}"
        )


in_stock = sum(
    1
    for status in statuses
    if status.startswith("🟢")
)


out_of_stock = sum(
    1
    for status in statuses
    if status.startswith("🔴")
)


errors = sum(
    1
    for status in statuses
    if status.startswith("⚠️")
)


current_time = datetime.now(
    ZoneInfo("Europe/Amsterdam")
).strftime(
    "%d %b %Y, %H:%M"
)


lobbes_results = check_lobbes_stock()


radar_data = {

    "last_checked": current_time,

    "shops": [
        {
    "name": "Drukke Mama's",
    "country": "🇧🇪 Belgium",
    "products": drukke_mamas_results
},
        {
    "name": "Spadt",
    "country": "🇧🇪 Belgium",
    "products": spadt_results
},
        {
    "name": "Houten Onderwijsmateriaal",
    "country": "🇧🇪 Belgium",
    "products": houten_results
},
        {
    "name": "DreamLand",
    "country": "🇳🇱 Netherlands",
    "products": dreamland_results
},
        {
    "name": "Smyths Toys",
    "country": "🇳🇱 Netherlands",
    "products": smyths_results
},
                {
            "name": "Intertoys",

            "country": "🇳🇱 Netherlands",

            "products": intertoys_results

        },

        {

            "name": "Toys42Hands",

            "country": "🇳🇱 Netherlands",

            "products": [

                {

                    "name": product["name"],

                    "url": product["url"],

                    "status": (

                        "in_stock"

                        if statuses[i].startswith("🟢")

                        else

                        "out_of_stock"

                        if statuses[i].startswith("🔴")

                        else

                        "error"

                    )

                }

                for i, product
                in enumerate(products)

            ]

        },


        {

            "name": "Lobbes",

            "country": "🇳🇱 Netherlands",

            "products": lobbes_results

        }

    ]

}


with open(
    "radar.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        radar_data,
        file,
        indent=2,
        ensure_ascii=False
    )


lobbes_in_stock = sum(
    1
    for product in lobbes_results
    if product["status"] == "in_stock"
)

lobbes_out_of_stock = sum(
    1
    for product in lobbes_results
    if product["status"] == "out_of_stock"
)

lobbes_errors = sum(
    1
    for product in lobbes_results
    if product["status"] == "error"
)


lobbes_statuses = []

for product in lobbes_results:

    if product["status"] == "in_stock":

        lobbes_statuses.append(
            f"🟢 {product['name']}"
        )

    elif product["status"] == "out_of_stock":

        lobbes_statuses.append(
            f"🔴 {product['name']}"
        )

    else:

        lobbes_statuses.append(
            f"⚠️ {product['name']}"
        )


radar_message = (

    "📡 NEEDOH LIVE RADAR\n\n"

    "🛍️ Toys42Hands 🇳🇱\n\n"

    + "\n".join(statuses)

    + "\n\n"

    + f"🟢 In stock: {in_stock}\n"

    + f"🔴 Out of stock: {out_of_stock}\n"

    + f"⚠️ Could not check: {errors}\n\n"

    "🛍️ Lobbes 🇳🇱\n\n"

    + "\n".join(lobbes_statuses)

    + "\n\n"

    + f"🟢 In stock: {lobbes_in_stock}\n"

    + f"🔴 Out of stock: {lobbes_out_of_stock}\n"

    + f"⚠️ Could not check: {lobbes_errors}\n\n"

    + f"🕐 Last checked: {current_time}"

)



print(
    "✅ Stock check completed!"
)

print(
    "ℹ️ Duplicate-alert protection is active."
)
