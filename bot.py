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

send_telegram(

    radar_message,

    RADAR_URL

)


print(
    "📡 Radar sent to Telegram!"
)

print(
    "✅ Stock check completed!"
)

print(
    "ℹ️ Duplicate-alert protection is active."
)
