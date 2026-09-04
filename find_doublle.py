import pandas as pd

# --- настройки ---
input_file = "group_target/all_groups.xlsx"          # исходный файл
output_file = "group_target/target_gr.xlsx"        # результат
column_name = "Группы"   # столбец, по которому ищем дубли
sheet_name = 1                    # лист (0 = первый, или имя листа строкой)

# читаем
df = pd.read_excel(input_file, sheet_name=sheet_name)

# сколько было дублей
before = len(df)
df = df.drop_duplicates(subset=[column_name], keep="first")
after = len(df)

print(f"Было строк: {before}")
print(f"Стало строк: {after}")
print(f"Удалено дублей: {before - after}")

# сохраняем
df.to_excel(output_file, index=False)
print(f"Сохранено в {output_file}")