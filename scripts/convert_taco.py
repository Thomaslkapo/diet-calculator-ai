# Converts the official TACO spreadsheet (NEPA/UNICAMP, 4th edition, 2011)
# into a simple CSV with only the columns the diet calculator needs.
#
# Run from the project root:
#   python scripts/convert_taco.py

import csv
import xlrd

INPUT_FILE = "data/raw/taco_4a_edicao_2011.xls"
OUTPUT_FILE = "data/taco.csv"

# column number of each value in the spreadsheet (found with explore_taco.py)
COLUMNS = {
    "id": 0,
    "food": 1,
    "kcal": 3,
    "protein": 5,
    "fat": 6,
    "carbs": 8,
    "fiber": 9,
}


def clean_value(value):
    # turns a spreadsheet cell into a number (or empty when there is no data)
    if value == "Tr":
        # "Tr" (trace) = an amount too small to measure
        return 0.0
    if isinstance(value, float):
        return round(value, 1)
    # "NA" (not applicable), "*" (being reviewed) or an empty cell
    return ""


book = xlrd.open_workbook(INPUT_FILE)
sheet = book.sheet_by_index(0)

foods = []
category = ""

for i in range(sheet.nrows):
    row = sheet.row_values(i)
    first_cell = row[0]

    if isinstance(first_cell, float):
        # a number in the first column = a food row
        foods.append({
            "id": int(first_cell),
            # split + join removes extra spaces (e.g. "Coco,  verde" -> "Coco, verde")
            "food": " ".join(row[COLUMNS["food"]].split()),
            "category": category,
            "kcal": clean_value(row[COLUMNS["kcal"]]),
            "protein": clean_value(row[COLUMNS["protein"]]),
            "fat": clean_value(row[COLUMNS["fat"]]),
            "carbs": clean_value(row[COLUMNS["carbs"]]),
            "fiber": clean_value(row[COLUMNS["fiber"]]),
        })
    elif first_cell.strip() and all(cell in ("", " ") for cell in row[1:]):
        # text only in the first column = a category title (e.g. "Cereais e derivados")
        category = first_cell.strip()

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "food", "category", "kcal", "protein", "fat", "carbs", "fiber"])
    writer.writeheader()
    writer.writerows(foods)

print(f"{len(foods)} foods saved to {OUTPUT_FILE}")
