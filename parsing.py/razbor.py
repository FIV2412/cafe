import pandas as pd

# Чтение файла (укажите правильный разделитель и кодировку)
df = pd.read_csv('products_nku.csv', delimiter=',', encoding='utf-8')

# Предположим, что наименование товара находится в колонке 'Название'
# Если колонка называется иначе, замените 'Название' на фактическое имя
column_name = 'Название'  # ← укажите вашу колонку

# Фильтрация строк, где значение колонки содержит фразу (без учёта регистра)
filtered = df[df[column_name].str.contains('частотный преобразователь', case=False, na=False)]

# Сохранение результата в новый файл
filtered.to_csv('products_filtered.csv', index=False, encoding='utf-8-sig')

print(f'Найдено строк: {len(filtered)}')
print(filtered.head())