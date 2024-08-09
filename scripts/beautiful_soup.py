import time
import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Initialize colorama
init()

# Headers to make the scraping less suspicious
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36"
}

# URL to scrape
base_url = ("https://www.booking.com/searchresults.en-gb.html?ss=United+States&ssne=United+States&ssne_untouched"
            "=United+States&efdco=1&label=gen173nr"
            "-1BCAEoggI46AdIM1gEaFCIAQGYAQm4ARnIAQ_YAQHoAQGIAgGoAgO4AvGOobUGwAIB0g"
            "IkZDA3MzAxMTktMmU4OC00NjhmLWI2YjQtMGNmZDRhN2FlMjA42AIF4AIB&sid=d91ee7"
            "1b81e445790c67ef3c7dfbd0f7&aid=304142&lang=en-gb&sb=1&src_elem=sb&src="
            "searchresults&dest_id=224&dest_type=country&checkin=2024-11-01"
            "&checkout=2025-01-19&group_adults=1&no_rooms=1&group_children=0")


# Scrape Single Page
def scrape_page(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    hotels = []
    for hotel in soup.find_all('div', attrs={'data-testid': 'property-card'}):
        try:
            name = hotel.find('div', attrs={'data-testid': 'title'}).text.strip()
        except AttributeError:
            name = 'N/A'

        try:
            location = hotel.find('span', attrs={'data-testid': 'address'}).text.strip()
        except AttributeError:
            location = 'N/A'

        try:
            price = hotel.find('span', attrs={'data-testid': 'price-and-discounted-price'}).text.strip()

        except AttributeError:
            price = 'N/A'

        hotels.append({
            'Name': name,
            'Location': location,
            'Price': price
        })

    return hotels


def scrape_all_pages(url, max_hotels):
    all_hotels = []
    page_number = 0
    cooldown_attempts = 0

    while True:
        url = f"{url}&offset={page_number * 25}"

        print(f"{Fore.CYAN}{'=' * 80}\nScraping page {page_number + 1}"
              f"\nURL: {url}\n{'=' * 80}{Style.RESET_ALL}")
        hotels = scrape_page(url)

        if not hotels:
            if cooldown_attempts == 0:
                print(f"{Fore.RED}No more hotels found, starting 1-minute cooldown.{Style.RESET_ALL}")
                for i in range(60, 0, -1):
                    print(f"{Fore.BLUE}Cooldown: {i} seconds remaining...{Style.RESET_ALL}", end='\r')
                    time.sleep(1)
                cooldown_attempts += 1
                continue  # Retry scraping the same page after cooldown
            else:
                print(f"{Fore.RED}No more hotels found after cooldown, stopping scrape.{Style.RESET_ALL}")
                break

        all_hotels.extend(hotels)
        total_hotels = len(all_hotels)

        print(f"{Fore.YELLOW}{'-' * 80}\nTotal hotels collected so far: {total_hotels}\n"
              f"{'-' * 80}{Style.RESET_ALL}")

        if total_hotels >= max_hotels:
            print(f"{Fore.GREEN}Reached the maximum limit of {max_hotels}"
                  f" hotels. Stopping scrape.{Style.RESET_ALL}")
            break

        page_number += 1
        cooldown_attempts = 0  # Reset cooldown attempts after successful scrape
        time.sleep(1)  # A bit of delay to avoid overloading the server

    return all_hotels


def scrape():
    max_hotels = 400

    # Scrape all pages

    all_hotels = scrape_all_pages(base_url, max_hotels)

    # Check if hotels were found
    if all_hotels:
        # Put the collected data into a DataFrame
        df = pd.DataFrame(all_hotels)

        # Save the data to an CSV file
        df.to_csv(Path.cwd().parent / 'data' / 'us_hotels.csv', index=False)

        print(f"{Fore.GREEN}\n{'=' * 80}\nData successfully saved in data/us_hotels.csv\n"
              f"{'=' * 80}{Style.RESET_ALL}")
    else:
        print(
            f"{Fore.RED}\n{'=' * 80}\nNo hotels found. Check the HTML structure of the page.\n{'=' * 80}"
            f"{Style.RESET_ALL}")


def main():
    scrape()


if __name__ == '__main__':
    main()
