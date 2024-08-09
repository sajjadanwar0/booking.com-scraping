import re
import time
from pathlib import Path

import pandas as pd
from colorama import Fore, Style, init
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# Initialize colorama
init()


# Initialize Selenium Web Driver

def initialize_selenium():
    options = Options()
    options.add_argument('-headless')
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_driver_path = "./chromedriver"
    driver = Chrome(service=Service(executable_path=chrome_driver_path, options=options))
    return driver


def spin_selenium():
    driver = initialize_selenium()

    url = "https://booking.com"

    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ada65db9b5')))

    driver.implicitly_wait(20)

    driver.maximize_window()
    return driver


def close_popup(driver):
    driver.get(driver.current_url)
    try:
        # check for popup window
        print("waiting for popup")
        popup_element = driver.find_element(
            By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']"
        )
        popup_element.click()
        print("closed")
    except NoSuchElementException:
        print("no popup element")


def change_currency(driver, currency=None):
    currency_element = driver.find_element(
        By.XPATH,
        "//button[contains(@data-testid,'header-currency-picker-trigger')]")
    currency_element.click()
    # choose a new currency
    currency = currency.upper()
    new_currency_element = driver.find_element(
        By.XPATH, f"//div[text()='{currency}']"
    )

    new_currency_element.click()


def search_place_to_go(driver, place):
    # destination field
    where_field = driver.find_element(By.NAME, "ss")
    where_field.clear()
    where_field.send_keys(place)
    time.sleep(1)  # sleep for 1s so website can load data
    first_option = driver.find_element(By.ID, "autocomplete-result-0")
    first_option.click()


def select_dates(driver, check_in_date, check_out_date):
    # select check in and check out dates
    check_in_element = driver.find_element(
        By.CSS_SELECTOR, f'span[data-date="{check_in_date}"]'
    )
    check_in_element.click()
    check_out_element = driver.find_element(
        By.CSS_SELECTOR, f'span[data-date="{check_out_date}"]'
    )
    check_out_element.click()


def select_details(driver, adults):
    # update number of adults, children, rooms
    selection_element = driver.find_element(
        By.CSS_SELECTOR, 'button[data-testid="occupancy-config"]'
    )
    selection_element.click()

    # adults

    while True:
        decrease_adults_button = driver.find_element(
            By.CLASS_NAME,
            "dba1b3bddf.e99c25fd33.aabf155f9a.f42ee7b31a.a86bcdb87f.af4d87ec2f",
        )
        decrease_adults_button.click()
        # getting the value of adults
        adults_value_element = driver.find_element(By.ID, "group_adults")
        adults_value = adults_value_element.get_attribute("value")
        if int(adults_value) == 1:
            break
    increase_adults_button = driver.find_element(
        By.CLASS_NAME,
        "dba1b3bddf.e99c25fd33.aabf155f9a.f42ee7b31a.a86bcdb87f.e137a4dfeb.d1821e6945",
    )

    for _ in range(adults - 1):
        increase_adults_button.click()


def click_search(driver):
    search_button = driver.find_element(
        By.CLASS_NAME,
        "dba1b3bddf.e99c25fd33.f8a5a77b19.f1c8772a7d.bec09c39da.f953867e0b.c437808707",
    )
    search_button.click()


# Scrape Single Page
def scrape_page(driver):
    hotel_boxes = driver.find_element(By.CSS_SELECTOR, 'div[class="f9958fb57b"]')

    hotels_cards = hotel_boxes.find_elements(
        By.CSS_SELECTOR, 'div[data-testid="property-card"]'
    )
    hotels = []
    for hotel in hotels_cards:
        try:
            name = (
                hotel.find_element(By.CSS_SELECTOR, 'div[data-testid="title"]')
                .get_attribute("innerHTML")
                .strip()
            ).replace("&amp;", " ")
        except AttributeError:
            name = 'N/A'

        try:
            location = (
                hotel.find_element(By.CSS_SELECTOR, 'span[data-testid="address"]')
                .get_attribute("innerHTML")
                .strip().replace("&nbsp;", " ")

            )

        except AttributeError:
            location = 'N/A'

        try:
            price = (
                hotel.find_element(
                    By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]'
                )
                .get_attribute("innerHTML")
                .strip().replace("&nbsp;", " ").removeprefix("US$")
            )
            price = re.sub("[^\d.]", "", price)

        except AttributeError:
            price = 'N/A'

        hotels.append({
            'Name': name,
            'Location': location,
            'Price': price
        })

    return hotels


def scrape_all_pages(driver, max_hotels):
    all_hotels = []
    page_number = 0
    cooldown_attempts = 0

    while True:
        current_url = f"{driver.current_url}&offset={page_number * 25}"

        print(
            f"{Fore.CYAN}{'=' * 80}\nScraping page {page_number + 1}\nURL: {current_url}\n{'=' * 80}{Style.RESET_ALL}")
        hotels = scrape_page(driver)

        if not hotels:
            if cooldown_attempts == 0:
                print(f"{Fore.RED}No more hotels found, starting 1-minute cooldown.{Style.RESET_ALL}")
                for i in range(60, 0, -1):
                    print(f"{Fore.BLUE}Cooldown: {i} seconds remaining...{Style.RESET_ALL}", end='\r')
                    time.sleep(1)
                cooldown_attempts += 1
                continue
            else:
                print(f"{Fore.RED}No more hotels found after cooldown, stopping scrape.{Style.RESET_ALL}")
                break

        all_hotels.extend(hotels)
        total_hotels = len(all_hotels)

        print(
            f"{Fore.YELLOW}{'-' * 80}\nTotal hotels collected so far: {total_hotels}  "
            f"out of : {max_hotels} \n{'-' * 80}"
            f"{Style.RESET_ALL}")

        if total_hotels >= int(max_hotels):
            print(f"{Fore.GREEN}Reached the maximum limit of {max_hotels} hotels. Stopping scrape.{Style.RESET_ALL}")
            break

        page_number += 1
        cooldown_attempts = 0  # Reset cooldown attempts after successful scrape
        time.sleep(1)  # A bit of delay to avoid overloading the server

    return all_hotels


def scrape(driver):
    time.sleep(1)
    max_hotels = 1

    try:
        hotel_numbers = driver.find_element(By.XPATH, "//div[@class='eda0d449dc a45957e294']").text
        max_hotels = re.sub("[^\d.]", "", hotel_numbers)
    except NoSuchElementException:
        pass

    # Scrape all pages

    all_hotels = scrape_all_pages(driver, max_hotels)

    # Check if hotels were found
    if all_hotels:
        # Put the collected data into a DataFrame
        df = pd.DataFrame(all_hotels)

        # Save the data to an CSV file
        df.to_csv(Path.cwd().parent / 'data' / 'us_hotels.csv', index=False)

        print(f"{Fore.GREEN}\n{'=' * 80}\nData successfully saved in data/us_hotels.csv\n{'=' * 80}{Style.RESET_ALL}")
    else:
        print(
            f"{Fore.RED}\n{'=' * 80}\nNo hotels found. "
            f"Check the HTML structure of the page.\n{'=' * 80}"
            f"{Style.RESET_ALL}")


def main():
    driver = spin_selenium()
    currency = input("Enter Currency Code (ex: USD , GBP, AUD):  ")
    change_currency(driver, currency)

    search_place_to_go(driver, place=input("Enter Destination: "))

    select_dates(driver,
                 check_in_date=input("Enter Check In Date: format yyyy-mm-dd: "),
                 check_out_date=input("Enter Check Out Date: "),
                 )

    select_details(driver, adults=int(input("Number of adults:")))
    click_search(driver)
    driver.refresh()
    time.sleep(5)
    scrape(driver)


if __name__ == '__main__':
    main()
