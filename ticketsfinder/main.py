import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

# ==== Telegram Configuration ====
# yurashB: 663980627
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = '663980627'
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# === Station IDs ===
# Київ: 2200001
# Сарни: 2218080

# ==== Train Search Configuration ====
FROM_ID = 2218080
TO_ID = 2200001
START_DATE = '2025-06-09'
TRAIN_URL = f"https://booking.uz.gov.ua/search-trips/2200001/2218000/list?startDate=2025-06-17"

MONITORED_TRAINS = [] # or [] to list all trains
CHECK_INTERVAL_SECONDS = 60


# ==== Main Loop ====
def monitor_trains():
    print("🚄 Monitor started...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    while True:
        try:
            with webdriver.Chrome(options=chrome_options) as driver:
                driver.get(TRAIN_URL)
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, "html.parser")

                all_tickets = extract_tickets(soup)
                matching_tickets = filter_tickets_by_train_name(all_tickets, MONITORED_TRAINS)

                if matching_tickets:
                    send_telegram_message("Квиток знайдено! 🎟️")
                    break

                print(f"[{datetime.now()}] No matching tickets. Found: {len(all_tickets)}")
        except Exception as e:
            print(f"Error occurred: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

# ==== Telegram ====
def send_telegram_message(text: str):
    try:
        response = requests.post(TELEGRAM_API, params={'chat_id': CHAT_ID, 'text': text})
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")


# ==== Ticket Parsing ====
def extract_tickets(soup: BeautifulSoup):
    result = []
    train_cards = soup.find_all("div", {
        "class": "Card bg-White p-4 md:p-5 shadow-Light rounded-[16px] md:rounded-[20px] TripUnit relative pt-10 !overflow-hidden w-full !transition !duration-[170ms] !ease-in-out hover:-translate-y-[3px] !shadow-Train hover:!shadow-TrainHover lg:!pr-0 cursor-pointer"})
    print(train_cards)
    for card in train_cards:
        try:
            train_name = card.find('div', class_='skew-x-12').get_text(strip=True)
            wagons = card.find_all('li')

            available_wagons = []
            for wagon in wagons:
                vagon_type = wagon.find('h4').get_text(strip=True)
                count = wagon.find('div',
                                   class_='Typography Typography--caption text-DarkGrey whitespace-nowrap md:group-hover:text-Primary').get_text(
                    strip=True)
                price = wagon.find('h3').get_text(strip=True)
                available_wagons.append({'type': vagon_type, 'count': count, 'price': price})

            result.append({'name': train_name, 'wagons': available_wagons})
        except Exception as e:
            print(f"Failed to parse a train card: {e}")
    return result



def filter_tickets_by_train_name(tickets, names):
    return [ticket for ticket in tickets if ticket['name'] in names]


if __name__ == "__main__":
    monitor_trains()
