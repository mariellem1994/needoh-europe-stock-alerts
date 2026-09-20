import os
import urllib.request
import urllib.parse

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# This will be filled in automatically in the next step
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = """🐿️ Needoh Europe Stock Alerts is online!

🇪🇺 Ready to hunt for Needohs!

🎃 Halloween
🎄 Christmas
✨ New releases
🛍️ European shops
🇬🇧 UK shops
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": message
}).encode()

request = urllib.request.Request(url, data=data)

with urllib.request.urlopen(request) as response:
    print(response.read().decode())
