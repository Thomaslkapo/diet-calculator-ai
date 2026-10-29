import csv

TACO_FILE = "data/taco.csv"


def to_number(text):
    # empty cell (no data) counts as 0
    if text == "":
        return 0.0
    return float(text)


def load_foods():
    # reads taco.csv and returns a dict: food id -> food data
    foods = {}
    with open(TACO_FILE, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            foods[row["id"]] = row
    return foods


def food_macros(food, grams):
    # TACO values are per 100 g, so scale them to the amount eaten
    factor = grams / 100
    return {
        "kcal": to_number(food["kcal"]) * factor,
        "protein": to_number(food["protein"]) * factor,
        "carbs": to_number(food["carbs"]) * factor,
        "fat": to_number(food["fat"]) * factor,
    }


foods = load_foods()
rice = foods["3"]
print(rice["food"])
print(food_macros(rice, 150))
