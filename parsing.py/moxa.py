def get_element_attribute(card, selector, attribute):
    """Безопасно получает атрибут дочернего элемента карточки."""
    try:
        element = card.find_element(By.CSS_SELECTOR, selector)
        return element.get_attribute(attribute) or ""
    except (TimeoutException, WebDriverException, StaleElementReferenceException):
        return ""


def get_text_content(card, selector):
    """Получает текст элемента сначала через textContent, затем innerText."""
    for attribute in ("textContent", "innerText"):
        value = get_element_attribute(card, selector, attribute)
        value = clean_text(value)
        if value:
            return value
    return ""


def get_first_text(card, selectors):
    """Возвращает первый непустой текст по списку CSS-селекторов."""
    for selector in selectors:
        value = get_text_content(card, selector)
        if value:
            return value
    return ""


def parse_nnz_card(card):
    """Извлекает данные из корректной карточки .catcard."""
    # Важно: передаём и обрабатываем именно контейнер товара .catcard.
    try:
        card = card.find_element(By.CSS_SELECTOR, ".catcard") \
            if "catcard" not in (card.get_attribute("class") or "").split() \
            else card
    except (TimeoutException, WebDriverException, StaleElementReferenceException):
        return {}

    # Основное наименование находится в a.catcard_name.
    # Используем textContent, затем innerText, так как .text может быть пустым.
    name = get_text_content(card, "a.catcard_name")

    # Fallback для вариантов разметки каталога.
    if not name:
        name = get_element_attribute(
            card,
            "meta[itemprop='name']",
            "content",
        )
        name = clean_text(name)

    if not name:
        name = get_text_content(card, "meta[itemprop='name']")

    description = get_first_text(
        card,
        (
            "[itemprop='description']",
            ".catcard_txt_hover",
            ".catcard_entry",
        ),
    )

    article = get_first_text(
        card,
        (
            '[itemprop="sku"]',
            ".catcard_article",
        ),
    )
    availability = get_text_content(card, ".availablebox")

    image = get_element_attribute(
        card,
        ".catcard_img img, img",
        "src",
    )
    if not image:
        image = get_element_attribute(
            card,
            ".catcard_img img, img",
            "data-src",
        )

    product_url = get_element_attribute(
        card,
        "a.catcard_name",
        "href",
    )
    if not product_url:
        product_url = get_element_attribute(
            card,
            "a[itemprop='url']",
            "href",
        )

    image = urljoin(NNZ_URL, image)
    product_url = urljoin(NNZ_URL, product_url)

    return {
        "source": "nnz-ipc.ru",
        "name": name,
        "description": description,
        "article": article,
        "product_code": "",
        "availability": availability,
        "image": image,
        "url": product_url,
    }


def parse_nnz_catalog(driver):
    """Загружает и обрабатывает все карточки каталога NNZ."""
    # Явно выбираем только корректные контейнеры карточек.
    cards = driver.find_elements(By.CSS_SELECTOR, ".catcard")
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
            print(f"NNZ: карточка {index}/{len(cards)} недоступна, пропуск")
            continue

        # Диагностический вывод первых трёх извлечённых наименований.
        if product["name"] and len(diagnostic_names) < 3:
            diagnostic_names.append(product["name"])
            print(
                f"NNZ: диагностика, название {len(diagnostic_names)}/3: "
                f"{product['name']}"
            )

        key = (
            product["article"],
            product["name"],
            product["url"],
        )

        if not any(key):
            print(f"NNZ: карточка {index}/{len(cards)} пустая, пропуск")
            continue

        if key in seen:
            print(f"NNZ: карточка {index}/{len(cards)} — дубликат")
            continue

        seen.add(key)
        products.append(product)
        print(
            f"NNZ: обработано {index}/{len(cards)}, "
            f"уникальных товаров: {len(products)}"
        )

    return products
