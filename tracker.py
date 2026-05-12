from playwright.sync_api import sync_playwright
import requests
import time
import re

# =====================================================
# CONFIG
# =====================================================

PLAYER_NAME = "ESTEBAN LEPAUL TOTS"

URL = "https://www.fut.gg/players/70415-esteban-lepaul/26-83956495/"

WEBHOOK_URL = "https://discord.com/api/webhooks/1503217947475316856/YfX9BYzXYf1clmxmlP_T_6vBzG9OHIJ_mMt_KvH_-CzTJpze59ErJ4e0eoRlRhko0kBF"

CHECK_INTERVAL = 15

# porcentaje mínimo para alertar
DISCOUNT_THRESHOLD = 0.70

# =====================================================

already_alerted = False


def send_alert(current_price, average_price, deal_percent):

    data = {
        "content": (
            f"🚨 @here PRICE ERROR DETECTADO 🚨\n\n"
            f"👤 {PLAYER_NAME}\n"
            f"💰 Lowest BIN: {current_price}\n"
            f"📊 Average: {average_price}\n"
            f"🔥 Deal: {deal_percent}% del promedio\n"
            f"🔗 {URL}"
        )
    }

    requests.post(WEBHOOK_URL, json=data)

    print("✅ ALERTA ENVIADA")


def parse_price(value):

    return int(value.replace(",", ""))


def extract_prices(text):

    # ==========================================
    # EXTINCT
    # ==========================================

    extinct = re.search(
        r"Lowest BIN\s+Extinct",
        text,
        re.IGNORECASE
    )

    if extinct:
        return None, None

    # ==========================================
    # LOWEST BIN
    # ==========================================

    lowest_match = re.search(
        r"Lowest BIN\s*(?:<\s*\d+\s*\w+\s*ago)?\s*([\d]{1,3}(?:,[\d]{3})+)",
        text,
        re.IGNORECASE
    )

    # ==========================================
    # AVERAGE
    # ==========================================

    average_match = re.search(
        r"Average\s*([\d]{1,3}(?:,[\d]{3})+)",
        text,
        re.IGNORECASE
    )

    if lowest_match and average_match:

        return (
            lowest_match.group(1),
            average_match.group(1)
        )

    return None, None


def check_player(browser):

    global already_alerted

    page = browser.new_page()

    page.goto(URL, timeout=60000)

    page.wait_for_timeout(5000)

    text = page.locator("body").inner_text()

    page.close()

    current_price, average_price = extract_prices(text)

    if not current_price or not average_price:

        print("❌ No hay datos")

        already_alerted = False

        return

    current = parse_price(current_price)
    average = parse_price(average_price)

    ratio = current / average

    print(f"💰 Current: {current_price}")
    print(f"📊 Average: {average_price}")
    print(f"📉 Ratio: {ratio:.2f}")

    # ==========================================
    # DETECTAR DEAL
    # ==========================================

    if ratio <= DISCOUNT_THRESHOLD:

        deal_percent = round(ratio * 100)

        if not already_alerted:

            print("🚨 PRICE ERROR DETECTADO")

            send_alert(
                current_price,
                average_price,
                deal_percent
            )

            already_alerted = True

    else:

        already_alerted = False

        print("🟡 Sin price error")


print(f"🔥 PRICE ERROR TRACKER - {PLAYER_NAME}")

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    while True:

        try:

            check_player(browser)

        except Exception as e:

            print("❌ ERROR:", e)

        time.sleep(CHECK_INTERVAL)