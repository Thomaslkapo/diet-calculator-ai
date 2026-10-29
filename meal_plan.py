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

def plan_totals(plan, foods):
    # adds up the macros of every food in the plan
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for item in plan:
        food = foods[item["id"]]
        macros = food_macros(food, item["grams"])
        for key in totals:
            totals[key] += macros[key]
    return totals


def compare_with_targets(totals, targets):
    # shows how far each total is from its target
    for key in targets:
        difference = totals[key] - targets[key]
        print(f"{key}: {totals[key]:.0f} / {targets[key]:.0f} (difference {difference:+.0f})")


foods = load_foods()

# test plan (later this will come from the AI)
plan = [
    {"id": "3", "grams": 150},
    {"id": "410", "grams": 200},
    {"id": "488", "grams": 100},
    {"id": "182", "grams": 100},
]

# targets from diet_calculator.py (test mode)
targets = {"kcal": 2187, "protein": 144, "carbs": 241, "fat": 72}

totals = plan_totals(plan, foods)
compare_with_targets(totals, targets)

