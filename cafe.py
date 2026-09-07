def print_drink(name, price):
    print(f"  - {name}: {price} руб.")


def print_menu(menu):
    for category, drinks in menu.items():
        print(f"\n{category}")
        total = 0
        for drink_name, drink_price in drinks.items():
            print_drink(drink_name, drink_price)
            total += drink_price
        print(f"Итого по категории '{category}': {total} руб.")


# Пример меню
coffee_menu = {
    "Кофе без молока": {"Эспрессо": 150, "Американо": 180},
    "Кофе с молоком": {"Капучино": 250, "Латте": 300,
                       "Капучино с корицей": 270},
    "Кофе со сливками": {"Раф": 350}
}

print_menu(coffee_menu)
#Добавьте функцию apply_discount(price, percent), которая применяет скидку к цене; * используйте эту функцию при выводе напитков со скидкой 10 %. 