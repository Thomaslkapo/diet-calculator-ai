from pytest import approx

from meal_plan import (
    MAX_FACTOR, MIN_FACTOR, fill_with_food, fit_macros, fit_with_fill, food_macros, load_foods, main_macro,
    plan_totals, scale_plan, substitute,
)

foods = load_foods()

# TACO ids used in the tests
BREAD = "53"  # Pão, trigo, francês
RICE = "3"  # Arroz, tipo 1, cozido
BANANA = "182"  # Banana, prata, crua
RAW_CHICKEN = "409"  # Frango, peito, sem pele, cru
BOILED_EGG = "488"  # Ovo, de galinha, inteiro, cozido
OLIVE_OIL = "259"  # Azeite, de oliva, extra virgem

TARGETS = {"kcal": 2187, "protein": 144, "carbs": 241, "fat": 72}


def day_plan():
    # the plan used in the README demo
    return [
        {"meal": "breakfast", "id": BREAD, "grams": 100},
        {"meal": "lunch", "id": RICE, "grams": 150},
        {"meal": "lunch", "id": RAW_CHICKEN, "grams": 200},
        {"meal": "dinner", "id": BOILED_EGG, "grams": 100},
    ]


def test_food_macros_scale_per_100g():
    # 200 g has exactly double the values of 100 g
    assert food_macros(foods[RICE], 200)["carbs"] == approx(2 * food_macros(foods[RICE], 100)["carbs"])


def test_main_macro():
    assert main_macro(foods[RAW_CHICKEN]) == "protein"
    assert main_macro(foods[RICE]) == "carbs"
    assert main_macro(foods[OLIVE_OIL]) == "fat"


def test_substitute_bread_for_rice():
    # the README example: 100 g of French bread = 209 g of rice (same carbs)
    assert substitute(foods, BREAD, 100, RICE, "carbs") == approx(209, abs=1)


def test_substitute_keeps_the_macro():
    grams = substitute(foods, RICE, 200, BANANA, "carbs")
    assert food_macros(foods[BANANA], grams)["carbs"] == approx(food_macros(foods[RICE], 200)["carbs"])


def test_substitute_food_without_the_macro():
    # chicken has no carbs, so it can't replace rice
    assert substitute(foods, RICE, 200, RAW_CHICKEN, "carbs") is None


def test_scale_plan_hits_calories_and_keeps_fixed_food():
    plan = day_plan()
    plan[2]["fixed"] = True
    scaled = scale_plan(plan, foods, TARGETS["kcal"])
    assert plan_totals(scaled, foods)["kcal"] == approx(TARGETS["kcal"], abs=5)
    assert scaled[2]["grams"] == 200


def test_fit_macros_keeps_portions_within_limits():
    plan = day_plan()
    fitted = fit_macros(plan, foods, TARGETS)
    for start, item in zip(plan, fitted):
        # +1 / -1: grams are rounded to whole numbers
        assert start["grams"] * MIN_FACTOR - 1 <= item["grams"] <= start["grams"] * MAX_FACTOR + 1


def test_fit_macros_never_changes_fixed_food():
    plan = day_plan()
    plan[2]["fixed"] = True
    fitted = fit_macros(plan, foods, TARGETS)
    assert fitted[2]["grams"] == 200


def test_fill_carbs_hits_protein_and_calories():
    # protein used to end at 141 / 144 here: the target was lowered when chicken hit the limit
    fitted = fit_with_fill(day_plan(), foods, TARGETS, "carbs")
    totals = plan_totals(fitted, foods)
    assert totals["protein"] == approx(TARGETS["protein"], abs=1)
    assert totals["kcal"] == approx(TARGETS["kcal"], abs=5)


def test_fill_with_food_puts_the_rest_in_one_food():
    plan = day_plan() + [{"meal": "snack", "id": BREAD, "grams": 100}]
    filled = fill_with_food(plan, foods, TARGETS["kcal"], BREAD)
    assert plan_totals(filled, foods)["kcal"] == approx(TARGETS["kcal"], abs=5)
    # the other foods keep their amounts
    assert [item["grams"] for item in filled[1:4]] == [150, 200, 100]
    # the bread was 100 g in both meals, so the extra is split in half
    assert filled[0]["grams"] == approx(filled[4]["grams"], abs=1)
