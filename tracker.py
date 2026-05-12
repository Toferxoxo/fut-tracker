import requests
from bs4 import BeautifulSoup
import time
import re

# =====================================================
# CONFIG
# =====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1503841297256022038/6RDdh0dwhvCwq3sAokbyX3wHxiSVf6DQ_p_mo4zhJYoHGmKWyinLHwpi70Wxe9FDM442"

CHECK_INTERVAL = 300

MAX_PAGES = 3

MIN_PRICE = 50000

DISCOUNT_THRESHOLD = 0.65

# =====================================================

already_alerted = {}

# =====================================================


def send_alert(name, price, average, ratio, url):

    percent = round(ratio * 100)

    data = {
        "content": (
            f"🚨 @here POSIBLE PRICE ERROR 🚨\n\n"
            f"👤 {name}\n"
            f"💰 BIN: {price:,}\n"
            f"📊 AVG: {average:,}\n"
            f"🔥 Ratio: {percent}%\n"
            f"🔗 {url}"
        )
    }

    response = requests.post(
        WEBHOOK_URL,
        json=data
    )

    if response.status_code == 204:

        print(f"✅ ALERTA [{name}]")

    else:

        print(f"❌ ERROR ALERTA [{name}]")


# =====================================================


def parse_price(text):

    text = text.replace(",", "")

    digits = re.findall(r"\d+", text)

    if digits:

        return int("".join(digits))

    return None


# =====================================================


def get_player_links(page):

    url = f"https://www.futbin.com/players?page={page}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/player/" in href:

            full_url = "https://www.futbin.com" + href

            links.append(full_url)

    return list(set(links))


# =====================================================


def check_player(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text(" ", strip=True)

    # ==========================================
    # NAME
    # ==========================================

    title = soup.title.text.strip()

    # ==========================================
    # LOWEST PRICE
    # ==========================================

    lowest_match = re.search(
        r"LCPrice2\":\s*\"([\d,]+)\"",
        response.text
    )

    if not lowest_match:

        return

    current_price = parse_price(
        lowest_match.group(1)
    )

    if not current_price:

        return

    # ==========================================
    # FAKE AVERAGE CALCULATION
    # ==========================================

    average_price = int(current_price * 1.6)

    if current_price < MIN_PRICE:

        return

    ratio = current_price / average_price

    print(
        f"👤 {title[:50]} | "
        f"{current_price:,} | "
        f"ratio {ratio:.2f}"
    )

    # ==========================================
    # ALERT
    # ==========================================

    if ratio <= DISCOUNT_THRESHOLD:

        if url not in already_alerted:

            send_alert(
                title,
                current_price,
                average_price,
                ratio,
                url
            )

            already_alerted[url] = True

    else:

        if url in already_alerted:

            del already_alerted[url]


# =====================================================

print("🔥 FUTBIN GLOBAL SCANNER")

while True:

    try:

        for page in range(1, MAX_PAGES + 1):

            print(f"📄 PAGE {page}")

            players = get_player_links(page)

            print(f"🔎 {len(players)} players")

            for player_url in players:

                try:

                    check_player(player_url)

                    time.sleep(2)

                except Exception as e:

                    print("❌ PLAYER ERROR", e)

    except Exception as e:

        print("❌ LOOP ERROR", e)

    print("😴 SLEEPING")

    time.sleep(CHECK_INTERVAL)