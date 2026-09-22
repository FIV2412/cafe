import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

NNZ_URL = (
    "https://nnz-ipc.ru/catalogue/comm/ethernet/?pa=3&"
    "filter%5Bc5de0343-a8d4-46b6-9651-07eb9bc5f57e%5D"
    "%5B113823%5D=MOXA%E2%80%83"
)
OUTPUT_FILE = "nnz_products.csv"
CARD_SELECTOR = ".catcard"


def clean_text(value):
    return re.sub(r"\\s+", " ", str(value or "")).strip()


def get_element_attribute(card, selector, attribute):
    try:
        element = card.find_element(By.CSS_SELECTOR, selector)
        return element.get_attribute(attribute) or ""
    except (TimeoutException, WebDriverException, StaleElementReferenceException):
        return ""


def get_text_content(card, selector):
    for attribute in ("textContent", "innerText"):
        value = get_element_attribute(card, selector, attribute)
        value = clean_text(value)
        if value:
            return value
    return ""


def get_first_text(card, selectors):
    for selector in selectors:
        value = get_text_content(card, selector)
        if value:
            return value
    return ""


def parse_nnz_card(card):
    try:
        card = (
            card.find_element(By.CSS_SELECTOR, ".catcard")
            if "catcard" not in (card.get_attribute("class") or "").split()
            else card
        )
    except (TimeoutException, WebDriverException, StaleElementReferenceException):
        return {}

    name = get_text_content(card, "a.catcard_name")
    if not name:
        name = clean_text(get_element_attribute(card, "meta[itemprop='name']", "content"))
    if not name:
        name = get_text_content(card, "meta[itemprop='name']")

    description = get_first_text(card, (
        "[itemprop='description']",
        ".catcard_txt_hover",
        ".catcard_entry",
    ))
    article = get_first_text(card, (
        '[itemprop="sku"]',
        ".catcard_article",
    ))
    availability = get_text_content(card, ".availablebox")

    image = get_element_attribute(card, ".catcard_img img, img", "src")
    if not image:
        image = get_element_attribute(card, ".catcard_img img, img", "data-src")

    product_url = get_element_attribute(card, "a.catcard_name", "href")
    if not product_url:
        product_url = get_element_attribute(card, "a[itemprop='url']", "href")

    return {
        "source": "nnz-ipc.ru",
        "name": name,
        "description": description,
        "article": article,
        "product_code": "",
        "availability": availability,
        "image": urljoin(NNZ_URL, image),
        "url": urljoin(NNZ_URL, product_url),
    }

def load_all_products(driver):
    """
    Загружает товары нажатием кнопки «Ещё».
    После каждого нажатия ждёт увеличения количества .catcard.
    """

    more_xpath = (
        "//*[self::button or self::a]"
        "[contains(translate(normalize-space(.), "
        "'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', "
        "'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'), 'ещё') "
        "or contains(translate(normalize-space(.), "
        "'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', "
        "'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'), 'еще')]"
    )

    previous_count = 0

    for attempt in range(300):
        cards = driver.find_elements(
            By.CSS_SELECTOR,
            ".catcard",
        )
        current_count = len(cards)

        print(
            f"Загрузка {attempt + 1}: "
            f"найдено карточек {current_count}"
        )

        buttons = driver.find_elements(By.XPATH, more_xpath)

        visible_buttons = []
        for button in buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    visible_buttons.append(button)
            except StaleElementReferenceException:
                continue

        if not visible_buttons:
            print("Кнопка «Ещё» не найдена или больше отсутствует.")
            break

        button = visible_buttons[0]

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                button,
            )
            time.sleep(1)

            driver.execute_script(
                "arguments[0].click();",
                button,
            )

            WebDriverWait(driver, 20).until(
                lambda d: len(
                    d.find_elements(
                        By.CSS_SELECTOR,
                        ".catcard",
                    )
                ) > current_count
            )

            time.sleep(2)

        except TimeoutException:
            new_count = len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    ".catcard",
                )
            )

            print(
                f"После нажатия было {current_count}, "
                f"стало {new_count}"
            )

            if new_count <= current_count:
                print("Новые товары не появились. Загрузка остановлена.")
                break

        except StaleElementReferenceException:
            time.sleep(2)
            continue

        if current_count == previous_count:
            print("Количество товаров не изменилось. Остановка.")
            break

        previous_count = current_count

    return driver.find_elements(
        By.CSS_SELECTOR,
        ".catcard",
    )



def parse_nnz_catalog(driver):
    cards = load_all_products(driver)
    products = []
    seen = set()
    diagnostic_names = []

    print(f"NNZ: найдено карточек для обработки: {len(cards)}")
    print("NNZ: обработка карточек...")

    for index, card in enumerate(cards, start=1):
        try:
            product = parse_nnz_card(card)
        except StaleElementReferenceException:
            print(f"NNZ: карточка {index} устарела, пропуск")
            continue

        if not product:
            continue

        if product["name"] and len(diagnostic_names) < 3:
            diagnostic_names.append(product["name"])
            print(f"NNZ: название {len(diagnostic_names)}/3: {product['name']}")

        key = (product["article"], product["name"], product["url"])
        if not any(key) or key in seen:
            continue

        seen.add(key)
        products.append(product)
        print(f"NNZ: обработано {index}/{len(cards)}, уникальных товаров: {len(products)}")

    return products


def save_products(products):
    fieldnames = [
        "source", "name", "description", "article",
        "product_code", "availability", "image", "url",
    ]

    try:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(products)
    except PermissionError:
        backup = Path(OUTPUT_FILE).with_name("nnz_products_backup.csv")
        with backup.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(products)
        print(f"Основной CSV занят. Сохранено в {backup}")


def main():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(NNZ_URL)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)
        products = parse_nnz_catalog(driver)
        save_products(products)
        print(f"Готово. Сохранено товаров: {len(products)}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
