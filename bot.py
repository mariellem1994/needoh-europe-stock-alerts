import os
import urllib.request
import urllib.parse
import json
import re
from html import unescape
from urllib.parse import urljoin
from datetime import datetime
from zoneinfo import ZoneInfo
import time


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


RADAR_URL = "https://mariellem1994.github.io/needoh-europe-stock-alerts/"

print("🛡️ VERIFIED STOCK MODE V6 active — product-page confirmation required for non-Shopify stock alerts.")


sent_alert_keys = set()


def send_telegram(message, button_url=None):

    # Prevent the exact same Telegram message from being sent twice during
    # one execution, even if two checker paths encounter it.
    alert_key = message.strip()

    if alert_key in sent_alert_keys:

        print(
            "ℹ️ Duplicate Telegram alert suppressed in this run."
        )

        return None

    sent_alert_keys.add(
        alert_key
    )

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

    # Prefer the last published Live Radar state. A GitHub Actions job starts
    # from a fresh checkout, so the repository copy can otherwise be older
    # than the state produced by the previous bot run.
    remote_url = (
        RADAR_URL.rstrip("/")
        + "/radar.json?cache="
        + str(int(datetime.now().timestamp()))
    )

    try:

        request = urllib.request.Request(
            remote_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Cache-Control": "no-cache"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            remote_radar = json.loads(
                response.read().decode(
                    "utf-8",
                    errors="ignore"
                )
            )

        if (
            isinstance(remote_radar, dict)
            and isinstance(remote_radar.get("shops"), list)
        ):

            print(
                "✅ Loaded previous radar state from the Live Radar."
            )

            return remote_radar

    except Exception as error:

        print(
            f"ℹ️ Could not load Live Radar state: {error}"
        )

    try:

        with open(
            "radar.json",
            "r",
            encoding="utf-8"
        ) as file:

            local_radar = json.load(file)

        print(
            "ℹ️ Using repository radar.json as previous state."
        )

        return local_radar

    except Exception:

        print(
            "ℹ️ No previous radar data found. "
            "This run will be used as the baseline."
        )

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


        if (
            "alleen in de winkel te koop"
            in page_lower
        ):

            return "out_of_stock"


        if (
            "thuisbezorgen"
            in page_lower
        ):

            return "in_stock"


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
            "uit stock" in page_lower
            or
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
            '"availability":"https://schema.org/instock"' in page_lower
            or
            '"availability": "https://schema.org/instock"' in page_lower
            or
            '"availability":"instock"' in page_lower
            or
            '"availability": "instock"' in page_lower
        ):
            return "in_stock"

        return "out_of_stock"

    except Exception as e:

        print(
            f"⚠️ Spadt product error: {e}"
        )

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


dracek_collection_url = "https://www.dracek.cz/vyhledavani?search=Needoh"


def check_dracek_collection():

    try:

        request = urllib.request.Request(
            dracek_collection_url,
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

        print(f"⚠️ Dráček error: {e}")

        return None




def get_dracek_needoh_products(page):

    if not page:
        return []

    products = []
    seen_urls = set()

    anchor_pattern = re.compile(
        r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL
    )

    for match in anchor_pattern.finditer(page):

        href = unescape(match.group(1)).strip()
        name = clean_extra_product_name(match.group(2))

        combined = (name + " " + href).lower()

        if "needoh" not in combined and "nee-doh" not in combined:
            continue

        absolute_url = urljoin(
            dracek_collection_url,
            href
        )

        absolute_lower = absolute_url.lower()

        if (
            "vyhledavani" in absolute_lower
            or "search=" in absolute_lower
        ):
            continue

        if absolute_url in seen_urls:
            continue

        if len(name) < 3:
            slug = href.rstrip("/").split("/")[-1].split("?")[0]
            name = clean_extra_product_name(
                slug.replace("-", " ").replace("_", " ")
            )

        if "needoh" not in name.lower() and "nee-doh" not in name.lower():
            name = f"NeeDoh - {name}"

        products.append({
            "name": name,
            "url": absolute_url
        })

        seen_urls.add(absolute_url)

    return products


def check_dracek_product_stock(url):

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

        if "není skladem" in page_lower:
            return "out_of_stock"

        if "vyprodáno" in page_lower:
            return "out_of_stock"

        if "skladem" in page_lower:
            return "in_stock"

        return "out_of_stock"

    except Exception as e:

        print(
            f"⚠️ Dráček product error: {e}"
        )

        return "error"


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



# ============================================================
# EXTRA EUROPEAN NEEDOH SHOPS
# Added without changing the existing shop checkers above.
# These collection/search monitors automatically discover NeeDoh
# product links, show them on radar.json and use the existing
# previous-radar history for duplicate-safe Telegram alerts.
# ============================================================

extra_needoh_shops = [
    {
        "name": "Spellenrijk",
        "country": "🇳🇱 Netherlands",
        "url": "https://www.spellenrijk.nl/merk/1007/needoh.html"
    },
    {
        "name": "Proshop",
        "country": "🇳🇱 Netherlands",
        "url": "https://www.proshop.nl/?s=Needoh"
    },
    {
        "name": "Megaknihy",
        "country": "🇨🇿 Czech Republic",
        "url": "https://www.megaknihy.cz/vyhledavani?orderby=position&orderway=desc&search_query=Needoh&p=1"
    },
    {
        "name": "Dvě děti CZ",
        "country": "🇨🇿 Czech Republic",
        "url": "https://www.dvedeti.cz/vysledky-vyhledavani?search_keyword=Needoh&page=1"
    },
    {
        "name": "MimiMarket",
        "country": "🇨🇿 Czech Republic",
        "url": "https://www.mimimarket.cz/1208122646/e-search?q=Needoh"
    },
    {
        "name": "Monkey Mum",
        "country": "🇨🇿 Czech Republic",
        "url": "https://monkeymum.cz/search?q=needoh"
    },
    {
        "name": "Miss Lemonade",
        "country": "🇵🇱 Poland",
        "url": "https://misslemonade.pl/en/module/ambjolisearch/jolisearch?s=Needoh"
    },
    {
        "name": "Dzieciaki Bystrzaki",
        "country": "🇵🇱 Poland",
        "url": "https://www.dzieciakibystrzaki.pl/szukaj?controller=search&orderby=position&orderway=desc&search-cat-select=0&search_query=Needoh&submit_search="
    },
    {
        "name": "Tublu",
        "country": "🇦🇹 Austria",
        "shopify": True,
        "url": "https://tublu.at/search?page=1&q=needoh&type=product"
    },
    {
        "name": "Dve Deti SK",
        "country": "🇸🇰 Slovakia",
        "url": "https://www.dvedeti.sk/vysledky-vyhladavania?search_keyword=Needoh&page=1"
    },
    {
        "name": "Ken Black",
        "country": "🇮🇪 Ireland",
        "shopify": True,
        "shopify_collection": "needoh",
        "url": "https://kenblack.ie/search?sort_by=relevance&q=needoh&type=product&filter.v.availability=1&filter.v.price.gte=&filter.v.price.lte="
    },
    {
        "name": "Bizcocho de Yogur",
        "country": "🇪🇸 Spain",
        "url": "https://bizcochodeyogurshop.com/?s=needoh&post_type=product"
    },
    {
        "name": "Logopedicum",
        "country": "🌍 Europe",
        "url": "https://logopedicum.com/?mot_q=Needoh"
    },
    {
        "name": "2KidsToys",
        "country": "🌍 Europe",
        "url": "https://www.2kidstoys.com/search-results?search_keyword=Needoh&page=1"
    },
    {
        "name": "Toy Corner",
        "country": "🇮🇪 Ireland",
        "shopify": True,
        "shopify_collection": "nee-doh",
        "url": "https://toycorner.ie/collections/nee-doh"
    },
    {
        "name": "Funny Bunny",
        "country": "🇬🇷 Greece",
        "url": "https://www.funnybunny.gr/?s=Nee+doh&post_type=product&dgwt_wcas=1"
    },
    {
        "name": "Mavros Larnaca",
        "country": "🇨🇾 Cyprus",
        "url": "https://mavroslarnaca.com/?s=Needoh&post_type=product"
    },
    {
        "name": "MiniCool",
        "country": "🇵🇹 Portugal",
        "shopify": True,
        "url": "https://minicool.pt/search?page=1&q=Needoh"
    },
    {
        "name": "Bavixo",
        "country": "🇨🇿 Czech Republic",
        "url": "https://www.bavixo.cz/search?phrase=Needoh"
    },
    {
        "name": "Thimble Toys",
        "country": "🇳🇱 Netherlands",
        "url": "https://www.thimbletoys.com/nl/zoek/Needoh/all"
    },
    {
        "name": "Müller",
        "country": "🇩🇪 Germany",
        "url": "https://www.mueller.de/search/?q=Needoh"
    },
    {
        "name": "Juguetea",
        "country": "🇪🇸 Spain",
        "url": "https://juguetea.es/?s=Needoh&post_type=product"
    },
    {
        "name": "Le Monde Imaginaire",
        "country": "🇫🇷 France",
        "url": "https://lemondeimaginaire.com/?q=Needoh"
    },
    {
        "name": "Booghe",
        "country": "🇬🇧 United Kingdom",
        "shopify": True,
        "url": "https://www.booghe.co.uk/search?type=article%2Cpage%2Cproduct&q=Needoh*"
    },
    {
        "name": "Lekia",
        "country": "🇸🇪 Sweden",
        "url": "https://www.lekia.se/sokresultat?q=Needoh&tab_index=0"
    }
]


def fetch_extra_shop_page(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
        "Cache-Control": "no-cache"
    }

    try:

        request = urllib.request.Request(
            url,
            headers=headers
        )

        with urllib.request.urlopen(
            request,
            timeout=25
        ) as response:

            return response.read().decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as direct_error:

        # Some European stores block GitHub Actions IPs with 403/5xx.
        # Jina Reader is used only as a read-only fallback for the same
        # public page; it often makes those public search pages readable.
        reader_url = "https://r.jina.ai/http://" + url.replace(
            "https://",
            ""
        ).replace(
            "http://",
            ""
        )

        try:

            request = urllib.request.Request(
                reader_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "text/plain,*/*"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=35
            ) as response:

                page = response.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            print(
                f"ℹ️ Direct request blocked; reader fallback worked for {url}"
            )

            return page

        except Exception:

            raise direct_error


def clean_extra_product_name(value):

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        " ",
        value
    )

    value = unescape(value)

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value[:180]


def infer_extra_stock(section):

    text = clean_extra_product_name(section).lower()

    out_markers = [
        "out of stock",
        "sold out",
        "sold-out",
        "unavailable",
        "coming soon",
        "due ",
        "niet op voorraad",
        "niet leverbaar",
        "niet meer leverbaar",
        "momenteel niet leverbaar",
        "binnenkort beschikbaar",
        "uitverkocht",
        "tijdelijk uitverkocht",
        "není skladem",
        "neni skladem",
        "momentálně není dostupný",
        "momentalne neni dostupny",
        "vyprodáno",
        "vyprodano",
        "nedostupné",
        "nedostupne",
        "brak w magazynie",
        "brak na stanie",
        "wyprzedane",
        "agotado",
        "esgotado",
        "épuisé",
        "epuise",
        "nicht verfügbar",
        "nicht verfugbar",
        "ausverkauft",
        "ej i lager",
        "slutsåld",
        "slutsald"
    ]

    in_markers = [
        "in stock",
        "op voorraad",
        "direct leverbaar",
        "bestel",
        "skladem",
        "dostupné",
        "dostupne",
        "na stanie",
        "w magazynie",
        "disponible",
        "em stock",
        "en stock",
        "auf lager",
        "i lager",
        "add to cart",
        "add to basket",
        "do koszyka",
        "do košíku",
        "do kosiku",
        "añadir al carrito",
        "adicionar ao carrinho"
    ]

    if any(
        marker in text
        for marker in out_markers
    ):
        return "out_of_stock"

    if any(
        marker in text
        for marker in in_markers
    ):
        return "in_stock"

    return "unknown"


def get_shopify_needoh_products(shop):

    parsed = urllib.parse.urlparse(
        shop["url"]
    )

    base_url = (
        f"{parsed.scheme}://{parsed.netloc}"
    )

    collection = shop.get(
        "shopify_collection"
    )

    if collection:

        json_url = (
            f"{base_url}/collections/"
            f"{collection}/products.json?limit=250"
        )

    else:

        json_url = (
            f"{base_url}/products.json?limit=250"
        )

    try:

        request = urllib.request.Request(
            json_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8",
                    errors="ignore"
                )
            )

    except Exception as error:

        print(
            f"ℹ️ {shop['name']} Shopify feed unavailable: {error}"
        )

        return None

    products_found = []

    for product in data.get(
        "products",
        []
    ):

        title = clean_extra_product_name(
            product.get("title", "")
        )

        handle = product.get(
            "handle",
            ""
        )

        vendor = str(
            product.get("vendor", "")
        )

        combined = (
            title
            + " "
            + handle
            + " "
            + vendor
        ).lower()

        if (
            "needoh" not in combined
            and "nee-doh" not in combined
            and "nee doh" not in combined
        ):
            continue

        variants = product.get(
            "variants",
            []
        )

        available = any(
            variant.get("available") is True
            for variant in variants
        )

        products_found.append({
            "name": title,
            "url": f"{base_url}/products/{handle}",
            "status": (
                "in_stock"
                if available
                else "out_of_stock"
            )
        })

    print(
        f"🔎 {shop['name']}: found {len(products_found)} NeeDoh products via Shopify feed"
    )

    return products_found


def get_extra_needoh_products(shop):

    if shop.get("shopify"):

        shopify_products = get_shopify_needoh_products(
            shop
        )

        if shopify_products is not None:
            return shopify_products

    try:

        page = fetch_extra_shop_page(
            shop["url"]
        )

    except Exception as error:

        print(
            f"⚠️ {shop['name']} collection error: {error}"
        )

        return []

    products_found = []
    seen_urls = set()

    link_matches = []

    # Normal HTML links.
    anchor_pattern = re.compile(
        r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL
    )

    for match in anchor_pattern.finditer(page):

        link_matches.append(
            (
                match.group(1),
                match.group(2),
                match.start(),
                match.end()
            )
        )

    # Markdown links from the reader fallback.
    markdown_pattern = re.compile(
        r"\[([^\]]{1,250})\]\((https?://[^)\s]+)\)",
        re.IGNORECASE
    )

    for match in markdown_pattern.finditer(page):

        link_matches.append(
            (
                match.group(2),
                match.group(1),
                match.start(),
                match.end()
            )
        )

    for href, raw_name, match_start, match_end in link_matches:

        href = unescape(
            href
        ).strip()

        name = clean_extra_product_name(
            raw_name
        )

        absolute_url = urljoin(
            shop["url"],
            href
        )

        combined = (
            name
            + " "
            + href
        ).lower()

        if (
            "needoh" not in combined
            and "nee-doh" not in combined
            and "nee doh" not in combined
        ):
            continue

        bad_url_markers = [
            "search_query=",
            "search_keyword=",
            "mot_q=",
            "?q=needoh",
            "?s=needoh",
            "/search?",
            "/vyhledavani?",
            "/vysledky-vyhled",
            "/szukaj?",
            "/sokresultat?",
            "jolisearch",
            "e-search",
            "/collections/nee-doh",
            "/collections/needoh",
            "/merk/1007/needoh",
            "/speelgoed/needoh"
        ]

        absolute_lower = absolute_url.lower()

        if any(
            marker in absolute_lower
            for marker in bad_url_markers
        ):
            continue

        if absolute_url in seen_urls:
            continue

        if len(name) < 3:

            slug = href.rstrip("/").split("/")[-1]
            slug = slug.split("?")[0]

            name = clean_extra_product_name(
                slug.replace("-", " ").replace("_", " ")
            )

        if (
            "needoh" not in name.lower()
            and "nee-doh" not in name.lower()
            and "nee doh" not in name.lower()
        ):

            if (
                "needoh" in absolute_lower
                or "nee-doh" in absolute_lower
            ):
                name = f"NeeDoh - {name}"
            else:
                continue

        section_start = max(
            0,
            match_start - 700
        )

        section_end = min(
            len(page),
            match_end + 1000
        )

        status = "unknown"

        products_found.append({
            "name": name,
            "url": absolute_url,
            "status": status
        })

        seen_urls.add(
            absolute_url
        )

    print(
        f"🔎 {shop['name']}: found {len(products_found)} NeeDoh product links"
    )

    return products_found


def get_previous_shop_products(
    previous_radar,
    shop_name
):

    if not previous_radar:
        return None

    for shop in previous_radar.get(
        "shops",
        []
    ):

        if shop.get("name") == shop_name:
            return shop.get("products", [])

    return None


def find_previous_extra_product(
    previous_products,
    product
):

    if previous_products is None:
        return None

    for previous_product in previous_products:

        if (
            previous_product.get("url") == product["url"]
            or previous_product.get("name") == product["name"]
        ):
            return previous_product

    return None



def verify_non_shopify_product_stock(shop, product):
    """
    Conservative product-page stock verifier for selected non-Shopify shops.
    Returns in_stock / out_of_stock / unknown.
    Search/category-page text is never accepted as stock proof.
    """

    supported_shops = {
        "Dvě děti CZ",
        "Dve Deti SK",
        "2KidsToys",
        "MimiMarket",
    }

    if shop.get("name") not in supported_shops:
        return "unknown"

    url = product.get("url", "")

    if not url:
        return "unknown"

    try:
        page = fetch_extra_shop_page(url)
    except Exception as error:
        print(
            f"⚠️ {shop['name']}: product-page verification failed for "
            f"{product.get('name', 'unknown product')}: {error}"
        )
        return "unknown"

    if not page:
        return "unknown"

    # Flatten enough markup/markdown to make exact phrases easier to detect.
    page_text = re.sub(r"<[^>]+>", " ", page)
    page_text = unescape(page_text)
    page_text = re.sub(r"\s+", " ", page_text).strip().lower()

    # Strong OUT signals first. These phrases mean the item is not currently
    # orderable from the shop, even if the page gives an estimated future
    # delivery time.
    out_markers = [
        "produkt bohužel nyní není v prodeji",
        "produkt bohuzel nyni neni v prodeji",
        "produkt bohužiaľ teraz nie je v predaji",
        "produkt bohuzial teraz nie je v predaji",
        "není skladem",
        "neni skladem",
        "není dostupné",
        "neni dostupne",
        "nie je skladom",
        "nie je dostupné",
        "nie je dostupne",
        "vyprodáno",
        "vyprodano",
        "vypredané",
        "vypredane",
        "out of stock",
        "sold out",
        "currently unavailable",
        "not available",
        "nedostupné",
        "nedostupne",
    ]

    if any(marker in page_text for marker in out_markers):
        return "out_of_stock"

    # Future/estimated delivery is NOT treated as in stock.
    future_markers = [
        "obvyklá doba dodání",
        "obvykla doba dodani",
        "odhadovaná doba dodání",
        "odhadovana doba dodani",
        "estimated delivery time",
        "doba dodania do",
        "na cestě do skladu",
        "na ceste do skladu",
        "na ceste na sklad",
    ]

    # Strong IN signals. Require explicit quantity/stock wording from the
    # product page rather than a generic "available" or "buy" button.
    in_patterns = [
        r"\bskladem\s+(?:\d+|1000\s+a\s+více)\s*ks\b",
        r"\bskladem\s+poslední\s+kus\b",
        r"\bposlední\s+kus\b",
        r"\bskladom\s+\d+\s*ks\b",
        r"\b\d+\s*(?:pcs|pc)\s+in\s+stock\b",
        r"\bin\s+stock\s*:\s*\d+\b",
        r"\b\d+\s+ks\s+skladem\b",
    ]

    if any(re.search(pattern, page_text) for pattern in in_patterns):
        return "in_stock"

    if any(marker in page_text for marker in future_markers):
        return "out_of_stock"

    return "unknown"


def apply_verified_extra_stock(shop, products):
    """
    Shopify keeps its structured variant availability.
    Selected non-Shopify stores are checked on each product page.
    Everything else stays UNKNOWN.
    """

    if shop.get("shopify"):
        return products

    verified = []

    for product in products:
        item = dict(product)
        item["status"] = verify_non_shopify_product_stock(
            shop,
            item
        )
        verified.append(item)

    return verified


def check_extra_needoh_shop(
    shop,
    previous_radar
):

    print(
        f"\nChecking {shop['name']}..."
    )

    products_found = get_extra_needoh_products(
        shop
    )

    products_found = apply_verified_extra_stock(
        shop,
        products_found
    )

    confirmed_in = sum(
        1 for product in products_found
        if product.get("status") == "in_stock"
    )
    confirmed_out = sum(
        1 for product in products_found
        if product.get("status") == "out_of_stock"
    )
    unverified = sum(
        1 for product in products_found
        if product.get("status") == "unknown"
    )

    if products_found:
        print(
            f"🔐 {shop['name']}: {confirmed_in} confirmed in stock, "
            f"{confirmed_out} confirmed out of stock, "
            f"{unverified} unverified"
        )

    previous_products = get_previous_shop_products(
        previous_radar,
        shop["name"]
    )

    if (
        not products_found
        and previous_products
    ):

        print(
            f"ℹ️ {shop['name']}: keeping previous radar products because this check returned none"
        )

        return previous_products

    # Baseline protection:
    # If an improved checker suddenly discovers a large catalogue that the
    # previous radar did not know about, silently learn that catalogue rather
    # than sending dozens of "new product" Telegram messages.
    previous_count = (
        len(previous_products)
        if previous_products
        else 0
    )

    newly_discovered = []

    for product in products_found:

        previous_product = find_previous_extra_product(
            previous_products,
            product
        )

        if previous_product is None:
            newly_discovered.append(
                product
            )

    first_baseline_run = (
        previous_products is None
    )

    catalogue_baseline_run = (
        first_baseline_run
        or (
            len(newly_discovered) >= 5
            and (
                previous_count == 0
                or len(newly_discovered) >= max(
                    5,
                    previous_count
                )
            )
        )
    )

    if catalogue_baseline_run and newly_discovered:

        print(
            f"ℹ️ {shop['name']}: silently baselining "
            f"{len(newly_discovered)} newly discovered products "
            f"(checker/catalogue expansion)"
        )

    for product in products_found:

        previous_product = find_previous_extra_product(
            previous_products,
            product
        )

        if (
            not catalogue_baseline_run
            and previous_product is None
            and product.get("status") == "in_stock"
        ):

            send_telegram(
                f"🆕 NEW NEEDOH FOUND!\n\n"
                f"➡️ {product['name']}\n"
                f"🛍️ {shop['name']}\n"
                f"{shop['country']}\n\n"
                f"🔗 {product['url']}",
                RADAR_URL
            )

            print(
                f"🆕 NEW {shop['name']} PRODUCT: {product['name']} (confirmed in stock)"
            )

        elif (
            not catalogue_baseline_run
            and previous_product is None
            and product.get("status") != "in_stock"
        ):
            # Keep the GitHub Actions log readable. Unverified discoveries are
            # retained in radar.json but never produce Telegram alerts.
            pass

        if previous_product is not None:

            previous_status = previous_product.get(
                "status"
            )

            # Strict stock alert: both sides must be trustworthy.
            # UNKNOWN -> IN STOCK does NOT alert. Only confirmed OUT -> confirmed IN.
            if (
                product.get("status") == "in_stock"
                and previous_status == "out_of_stock"
            ):

                send_telegram(
                    f"🚨 NEEDOH STOCK ALERT!\n\n"
                    f"➡️ {product['name']}\n"
                    f"🛍️ {shop['name']}\n"
                    f"{shop['country']}\n\n"
                    f"🟢 IN STOCK ONLINE!\n\n"
                    f"🔗 {product['url']}",
                    RADAR_URL
                )

                print(
                    f"🚨 BACK IN STOCK AT {shop['name']}: {product['name']}"
                )

    return products_found

previous_radar = load_previous_radar()


extra_shop_results = {}

for extra_shop in extra_needoh_shops:

    extra_shop_results[extra_shop["name"]] = check_extra_needoh_shop(
        extra_shop,
        previous_radar
    )



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
        and previous_radar
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
        and previous_radar
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


for product in mamiee_products:

    previous_status = get_previous_status(
        previous_radar,
        "Mamiee",
        product["name"]
    )

    if (
        previous_status is None
        and previous_radar
        and any(
            shop["name"] == "Mamiee"
            for shop in previous_radar.get("shops", [])
        )
    ):

        send_telegram(
            f"🚨 NEW NEEDOH FOUND!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Mamiee\n"
            f"🇨🇿 Czech Republic\n\n"
            f"🆕 NEW PRODUCT FOUND!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW MAMIEE NEEDOH: "
            f"{product['name']}"
        )


dracek_results = []

dracek_page = check_dracek_collection()

dracek_products = get_dracek_needoh_products(
    dracek_page
)

print(
    f"Found {len(dracek_products)} NeeDoh products at Dráček"
)

for product in dracek_products:

    print(
        f"Checking Dráček: {product['name']}"
    )

    current_status = check_dracek_product_stock(
        product["url"]
    )

    previous_status = get_previous_status(
        previous_radar,
        "Dráček",
        product["name"]
    )

    if (
        current_status == "in_stock"
        and previous_status == "out_of_stock"
    ):

        send_telegram(
            f"🚨 NEEDOH STOCK ALERT!\n\n"
            f"➡️ {product['name']}\n"
            f"🛍️ Dráček\n"
            f"🇨🇿 Czech Republic\n\n"
            f"🟢 BACK IN STOCK ONLINE!\n\n"
            f"🔗 {product['url']}"
        )

        print(
            f"🚨 NEW DRÁČEK STOCK: {product['name']}"
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

    dracek_results.append({
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

        *[
            {
                "name": extra_shop["name"],
                "country": extra_shop["country"],
                "products": extra_shop_results.get(
                    extra_shop["name"],
                    []
                )
            }
            for extra_shop in extra_needoh_shops
        ],

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
            "name": "Mamiee",
            "country": "🇨🇿 Czech Republic",
            "products": mamiee_results
        },

        {
            "name": "Dráček",
            "country": "🇨🇿 Czech Republic",
            "products": dracek_results
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
