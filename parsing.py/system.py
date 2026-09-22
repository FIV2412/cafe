# -*- coding: utf-8 -*-

import csv
import re
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

START_URL = "https://intelka-shop.ru/proizvoditeli/systeme-electric/?section=19"
PAGINATION_PARAMETER = "PAGEN_2"
FIRST_PAGE = 1
LAST_PAGE = 139

# Остальная логика без изменений:
# - извлечение name, article, product_code, availability и image;
# - удаление дублей;
# - промежуточное сохранение CSV через save_to_csv();
# - обработка PermissionError с сохранением в products_backup.csv
#   или в уникальный файл products_<timestamp>.csv.

# В цикле пагинации должны использоваться указанные настройки:
for page_number in range(FIRST_PAGE, LAST_PAGE + 1):
    params = {
        PAGINATION_PARAMETER: page_number,
    }
    # Далее оставить существующую логику загрузки и обработки страницы без изменений.
#START_URL = "https://intelka-shop.ru/proizvoditeli/oven/?section=16"
#PAGINATION_PARAMETER = "PAGEN_2"
#FIRST_PAGE = 1
#LAST_PAGE = 403
PAUSE_BETWEEN_PAGES = 1.5
OUTPUT_CSV = "products_nku.csv"
DIAGNOSTIC_CARDS_COUNT = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

CSV_FIELDS = [
    "name",
    "article",
    "product_code",
    "availability",
    "image",
]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def build_page_url(page_number: int) -> str:
    """Формирует URL страницы, сохраняя существующие параметры."""
    parts = urlsplit(START_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[PAGINATION_PARAMETER] = str(page_number)

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )


def extract_codes(codes_block) -> tuple[str, str]:
    """Извлекает артикул и код товара из блока с кодами."""
    if not codes_block:
        return "", ""

    raw_text = codes_block.get_text("\n", strip=True)
    lines = [clean_text(line) for line in raw_text.splitlines() if clean_text(line)]

    article = ""
    product_code = ""

    for line in lines:
        if not article and re.match(r"^Арт\.?\s*", line, re.IGNORECASE):
            value = re.sub(r"^Арт\.?\s*[:№#]?\s*", "", line, flags=re.IGNORECASE)
            article = value.split()[0] if value else ""

        if not product_code and re.match(r"^Код\s+товара\s*", line, re.IGNORECASE):
            value = re.sub(
                r"^Код\s+товара\s*[:№#]?\s*",
                "",
                line,
                flags=re.IGNORECASE,
            )
            product_code = value.split()[0] if value else ""

    if not article:
        match = re.search(r"Арт\.?\s*[:№#]?\s*([^\s|]+)", raw_text, re.IGNORECASE)
        if match:
            article = match.group(1).strip()

    if not product_code:
        match = re.search(
            r"Код\s+товара\s*[:№#]?\s*([^\s|]+)",
            raw_text,
            re.IGNORECASE,
        )
        if match:
            product_code = match.group(1).strip()

    return article, product_code


def _element_text(element) -> str:
    """Возвращает видимый текст элемента в нормализованном виде."""
    if not element:
        return ""
    return clean_text(element.get_text(" ", strip=True))


def _element_metadata(element) -> str:
    """Собирает текстовые значения атрибутов, в которых может быть статус."""
    if not element:
        return ""

    values = []
    for attribute in ("data-status", "title", "aria-label"):
        value = clean_text(element.get(attribute, ""))
        if value:
            values.append(value)

    return " ".join(values)


def _status_from_text(text: str) -> str:
    normalized = clean_text(text).casefold()
    if "под заказ" in normalized:
        return "Под заказ"
    if "в наличии" in normalized:
        return "В наличии"
    return ""


def extract_availability(card, diagnostic: bool = False) -> str:
    """
    Извлекает статус наличия.

    Пустые контейнеры с классами OutStock/InStock встречаются в каждой
    карточке, поэтому сам класс никогда не считается достаточным признаком.
    """
    labels_block = card.select_one(".productItemHorizontalLabels")
    out_element = card.select_one(".productItemHorizontalOutStock")
    in_element = card.select_one(".productItemHorizontalInStock")

    labels_text = _element_text(labels_block)
    out_text = _element_text(out_element)
    in_text = _element_text(in_element)

    if diagnostic:
        print(
            f"availability diagnostic: "
            f"labels_text={labels_text!r}, "
            f"out_text={out_text!r}, "
            f"in_text={in_text!r}"
        )

    for text in (labels_text, out_text, in_text):
        status = _status_from_text(text)
        if status:
            return status

    for element in (labels_block, out_element, in_element):
        status = _status_from_text(_element_metadata(element))
        if status:
            return status

    return ""


def extract_image(card) -> str:
    image = card.find("img")
    if not image:
        return ""

    image_url = (
        image.get("src")
        or image.get("data-src")
        or image.get("data-lazy-src")
        or image.get("data-original")
        or ""
    )
    return urljoin(START_URL, image_url)


def get_product_cards(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.productItemHorizontal")
    if not cards:
        cards = soup.select(".catalogList .productItemHorizontal")
    return cards


def parse_products(html: str) -> list[dict[str, str]]:
    cards = get_product_cards(html)
    products = []
    seen = set()

    for index, card in enumerate(cards):
        name_element = card.select_one("a.productItemHorizontalName")
        name = clean_text(
            name_element.get_text(" ", strip=True) if name_element else ""
        )

        codes_block = card.select_one(".productItemHorizontalCodes")
        article, product_code = extract_codes(codes_block)
        availability = extract_availability(
            card,
            diagnostic=index < DIAGNOSTIC_CARDS_COUNT,
        )
        image = extract_image(card)

        if not name and not article and not product_code:
            continue

        key = (name, article, product_code)
        if key in seen:
            continue

        seen.add(key)
        products.append(
            {
                "name": name,
                "article": article,
                "product_code": product_code,
                "availability": availability,
                "image": image,
            }
        )

    return products


def save_to_csv(products: list[dict[str, str]]) -> Path:
    output_path = Path(OUTPUT_CSV).resolve()

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(products)

    print(f"Сохранение CSV: {output_path} ({len(products)} товаров)")
    return output_path


def merge_products(
    products: list[dict[str, str]],
    new_products: list[dict[str, str]],
) -> int:
    existing_keys = {
        (item["name"], item["article"], item["product_code"])
        for item in products
    }
    added = 0

    for item in new_products:
        key = (item["name"], item["article"], item["product_code"])
        if key not in existing_keys:
            products.append(item)
            existing_keys.add(key)
            added += 1

    return added


def main() -> None:
    all_products: list[dict[str, str]] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)

        for page_number in range(FIRST_PAGE, LAST_PAGE + 1):
            progress = f"Страница {page_number}/{LAST_PAGE}"
            page_url = build_page_url(page_number)
            print(f"\n{progress}")
            print(f"Загрузка URL: {page_url}")

            response = session.get(page_url, timeout=30)
            print(f"HTTP-статус: {response.status_code}")
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            cards_count = len(get_product_cards(response.text))
            print(f"Количество карточек: {cards_count}")

            page_products = parse_products(response.text)
            added_count = merge_products(all_products, page_products)
            print(f"Количество новых товаров: {added_count}")
            print(f"Всего уникальных товаров: {len(all_products)}")
            print(f"{progress}: сохранение промежуточного результата")
            save_to_csv(all_products)

            if page_number < LAST_PAGE:
                print(f"Пауза перед следующей страницей: {PAUSE_BETWEEN_PAGES} сек.")
                time.sleep(PAUSE_BETWEEN_PAGES)

    print(f"\nСохранение итогового результата ({FIRST_PAGE}-{LAST_PAGE})")
    save_to_csv(all_products)
    print(f"Итоговое количество товаров: {len(all_products)}")


if __name__ == "__main__":
    main()
