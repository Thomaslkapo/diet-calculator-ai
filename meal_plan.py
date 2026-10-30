import csv
import json

import truststore
from dotenv import load_dotenv
from google import genai

TACO_FILE = "data/taco.csv"
MODEL = "gemini-3.1-flash-lite"

# use Windows' trusted certificates (needed when an antivirus inspects HTTPS)
truststore.inject_into_ssl()
# reads the .env file and loads GEMINI_API_KEY
load_dotenv()


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


def food_list_text(foods):
    # one line per food: id;name;kcal;protein;carbs;fat (per 100 g)
    lines = []
    for food in foods.values():
        if food["kcal"] == "":
            continue
        lines.append(f"{food['id']};{food['food']};{food['kcal']};{food['protein']};{food['carbs']};{food['fat']}")
    return "\n".join(lines)


def ask_ai_for_plan(foods, targets):
    # the AI only chooses foods and grams; Python checks the math afterwards
    prompt = f"""You are a nutritionist building a one-day meal plan for a Brazilian person.
Daily targets: {targets['kcal']} kcal, {targets['protein']} g protein, {targets['carbs']} g carbs, {targets['fat']} g fat.
Use ONLY foods from the list below. Values are per 100 g, in the format id;food;kcal;protein;carbs;fat.
Use common foods for breakfast, lunch, afternoon snack and dinner, and try to hit the targets.
Answer only with a JSON list where each item is: {{"meal": "...", "id": "...", "grams": number}}

{food_list_text(foods)}"""

    client = genai.Client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    plan = json.loads(response.text)
    for item in plan:
        # ids in taco.csv are text, so make sure the AI's ids are text too
        item["id"] = str(item["id"])
    return plan


def print_plan(plan, foods):
    # shows each food of the plan with its meal and grams
    for item in plan:
        print(f"{item['meal']}: {item['grams']} g {foods[item['id']]['food']}")


def substitute(foods, old_id, old_grams, new_id, macro):
    # grams of the new food that give the same amount of `macro` as the old food
    amount = food_macros(foods[old_id], old_grams)[macro]
    new_per_100g = to_number(foods[new_id][macro])
    if new_per_100g == 0:
        # the new food has none of this macro, so no amount can replace it
        return None
    return amount / new_per_100g * 100


def scale_plan(plan, foods, target_kcal):
    # grows or shrinks every portion by the same factor so the plan hits the calorie target;
    # fixed foods (an exact amount chosen by the user) never change
    fixed = [item for item in plan if item.get("fixed")]
    free = [item for item in plan if not item.get("fixed")]
    free_kcal = plan_totals(free, foods)["kcal"]
    if free_kcal == 0:
        # every food is fixed: nothing can change
        return [dict(item) for item in plan]
    factor = (target_kcal - plan_totals(fixed, foods)["kcal"]) / free_kcal
    scaled = []
    for item in plan:
        grams = item["grams"]
        if not item.get("fixed"):
            # round to whole grams, the precision of a kitchen scale
            grams = round(grams * factor)
        scaled.append({"meal": item["meal"], "id": item["id"], "grams": grams})
    return scaled


KCAL_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}
LOW_KCAL_LIMIT = 50  # foods under this (kcal per 100 g), like vegetables, keep their portion
MIN_FACTOR = 0.5  # a portion never drops below half of its starting amount
MAX_FACTOR = 2.0  # and never grows past double


def main_macro(food):
    # the macro that gives the most calories in this food: "protein", "carbs" or "fat"
    kcal_from = {}
    for macro in KCAL_PER_GRAM:
        kcal_from[macro] = to_number(food[macro]) * KCAL_PER_GRAM[macro]
    return max(kcal_from, key=kcal_from.get)


def fit_macros(plan, foods, targets, rounds=50, unlimited=None):
    # adjusts the grams group by group (protein, then fat, then carbs) until every macro hits its target,
    # keeping every portion between MIN_FACTOR and MAX_FACTOR times its starting amount;
    # the `unlimited` group ("carbs" or "fat") can grow past MAX_FACTOR
    fitted = [dict(item) for item in plan]
    for item in fitted:
        # remember the starting amount, to keep every portion within the limits
        item["start"] = item["grams"]
    for _ in range(rounds):
        for macro in ["protein", "fat", "carbs"]:
            group = []
            for item in fitted:
                if item.get("fixed"):
                    # the user chose this exact amount: never change it
                    continue
                food = foods[item["id"]]
                if to_number(food["kcal"]) >= LOW_KCAL_LIMIT and main_macro(food) == macro:
                    group.append(item)
            from_group = plan_totals(group, foods)[macro]
            if from_group == 0:
                continue
            from_others = plan_totals(fitted, foods)[macro] - from_group
            factor = max(targets[macro] - from_others, 0) / from_group
            for item in group:
                grams = item["grams"] * factor
                lowest = item["start"] * MIN_FACTOR
                grams = max(grams, lowest)
                if macro != unlimited:
                    grams = min(grams, item["start"] * MAX_FACTOR)
                item["grams"] = grams
    for item in fitted:
        # round to whole grams, the precision of a kitchen scale
        item["grams"] = round(item["grams"])
        del item["start"]
    return fitted


def fit_with_fill(plan, foods, targets, fill_with, rounds=10):
    # hits protein and calories: what the foods can't reach in the other macros
    # is moved, in calories, to the `fill_with` macro ("carbs" or "fat"),
    # whose foods have no MAX_FACTOR limit: the user asked them to fill the plan
    # (a macro the foods can't reach just keeps its foods at the MAX_FACTOR limit)
    fitted = fit_macros(plan, foods, targets, unlimited=fill_with)
    new_targets = dict(targets)
    for _ in range(rounds):
        missing_kcal = targets["kcal"] - plan_totals(fitted, foods)["kcal"]
        if abs(missing_kcal) < 1:
            break
        # move the missing calories to the fill macro and fit again
        new_targets[fill_with] += missing_kcal / KCAL_PER_GRAM[fill_with]
        fitted = fit_macros(plan, foods, new_targets, unlimited=fill_with)
    return fitted


def fill_with_food(plan, foods, target_kcal, fill_id):
    # every food keeps its amount; the `fill_id` food gets all the calories still missing
    # (if it is in more than one meal, the extra grams are split in proportion to each portion)
    fill_items = [item for item in plan if item["id"] == fill_id]
    others = [item for item in plan if item["id"] != fill_id]
    missing_kcal = max(target_kcal - plan_totals(others, foods)["kcal"], 0)
    fill_grams = missing_kcal / to_number(foods[fill_id]["kcal"]) * 100
    start_grams = sum(item["grams"] for item in fill_items)
    filled = []
    for item in plan:
        grams = item["grams"]
        if item["id"] == fill_id:
            if start_grams > 0:
                share = item["grams"] / start_grams
            else:
                share = 1 / len(fill_items)
            # round to whole grams, the precision of a kitchen scale
            grams = round(fill_grams * share)
        filled.append({"meal": item["meal"], "id": item["id"], "grams": grams})
    return filled


if __name__ == "__main__":
    foods = load_foods()

    # targets from diet_calculator.py (test mode)
    targets = {"kcal": 2187, "protein": 144, "carbs": 241, "fat": 72}

    plan = ask_ai_for_plan(foods, targets)
    print_plan(plan, foods)
    print()
    totals = plan_totals(plan, foods)
    compare_with_targets(totals, targets)

    print("\nOnly calories (scale_plan):")
    scaled = scale_plan(plan, foods, targets["kcal"])
    print_plan(scaled, foods)
    print()
    compare_with_targets(plan_totals(scaled, foods), targets)

    print("\nEvery macro (fit_macros):")
    fitted = fit_macros(plan, foods, targets)
    print_plan(fitted, foods)
    print()
    compare_with_targets(plan_totals(fitted, foods), targets)
    print()

    # substitution tests
    rice_to_banana = substitute(foods, "3", 200, "182", "carbs")
    print(f"200 g rice = {rice_to_banana:.0f} g banana (carbs)")

    bread_to_rice = substitute(foods, "53", 100, "3", "carbs")
    print(f"2 French breads (100 g) = {bread_to_rice:.0f} g rice (carbs)")

    cheese_to_egg = substitute(foods, "461", 50, "488", "protein")
    print(f"50 g minas cheese = {cheese_to_egg:.0f} g boiled egg (protein)")

    cooked_to_raw = substitute(foods, "408", 150, "409", "protein")
    print(f"150 g cooked chicken = {cooked_to_raw:.0f} g raw chicken (protein)")

    print(substitute(foods, "3", 200, "410", "carbs"))
