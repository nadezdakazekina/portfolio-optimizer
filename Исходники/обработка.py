import csv
import io
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path


# Английские названия месяцев, которые использует Investing.com
MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def normalize_header(value):
    """Приводит название столбца к единому виду."""
    return re.sub(r"[^a-z]", "", value.strip().lower())


def normalize_date(value):
    """Преобразует дату в формат YYYY-MM-DD."""
    value = value.strip()

    # Например: Oct 09, 2025
    match = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", value
    )

    if match:
        month_name, day, year = match.groups()
        month = MONTHS.get(month_name.lower())

        if month:
            try:
                parsed = datetime(int(year), month, int(day))
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                return None

    # Например: Oct 2025 — месячная запись без конкретного дня
    match = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", value)

    if match:
        month_name, year = match.groups()
        month = MONTHS.get(month_name.lower())

        if month:
            return f"{int(year):04d}-{month:02d}-01"

    # Другие распространённые форматы
    for fmt in (
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def normalize_price(value):
    """Подготавливает цену для числовых расчётов."""
    value = value.strip().replace("\u00a0", "").replace(" ", "")

    # На Investing.com запятая обычно разделяет тысячи:
    # 1,234.50 превращается в 1234.50
    value = value.replace(",", "")

    if value.lower() in ("", "-", "—", "n/a", "na"):
        return None

    return value


def find_columns(text):
    """Находит столбцы Date и Price даже при другом разделителе."""
    for delimiter in (",", ";", "\t"):
        rows = list(
            csv.reader(io.StringIO(text), delimiter=delimiter)
        )

        # Обычно заголовок находится в первой строке.
        for header_index, row in enumerate(rows[:30]):
            headers = [normalize_header(cell) for cell in row]

            if "date" in headers and "price" in headers:
                return (
                    rows,
                    header_index,
                    headers.index("date"),
                    headers.index("price"),
                )

    raise ValueError(
        "Не найдены столбцы Date и Price. "
        "Проверь, что выбран CSV-файл с Investing.com."
    )


def get_output_path(source_path):
    """Создаёт имя с (1), а при совпадении — с (2), (3) и т. д."""
    number = 1

    while True:
        output_path = source_path.with_name(
            f"{source_path.stem} ({number}).csv"
        )

        if not output_path.exists():
            return output_path

        number += 1


def main():
    root = tk.Tk()
    root.withdraw()

    try:
        selected_file = filedialog.askopenfilename(
            title="Выбери CSV-файл с Investing.com",
            filetypes=[("CSV-файлы", "*.csv"), ("Все файлы", "*.*")]
        )

        if not selected_file:
            return

        source_path = Path(selected_file)

        # Читаем CSV с поддержкой BOM
        try:
            text = source_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = source_path.read_text(encoding="cp1252")

        rows, header_index, date_index, price_index = find_columns(text)

        output_path = get_output_path(source_path)
        saved_rows = 0

        with output_path.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file, delimiter=",")

            # Заголовки для твоего инвестиционного приложения
            writer.writerow(["date", "close"])

            for row in rows[header_index + 1:]:
                if len(row) <= max(date_index, price_index):
                    continue

                date_value = normalize_date(row[date_index])
                price_value = normalize_price(row[price_index])

                if date_value is None or price_value is None:
                    continue

                writer.writerow([date_value, price_value])
                saved_rows += 1

        if saved_rows == 0:
            output_path.unlink(missing_ok=True)
            raise ValueError(
                "Не удалось найти строки с корректными датами и ценами."
            )

        messagebox.showinfo(
            "Готово!",
            f"Обработка завершена.\n\n"
            f"Строк сохранено: {saved_rows}\n"
            f"Файл:\n{output_path}"
        )

    except Exception as error:
        messagebox.showerror("Ошибка", str(error))

    finally:
        root.destroy()


if __name__ == "__main__":
    main()