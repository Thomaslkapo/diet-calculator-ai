import csv


def to_number(text):
    # empty cell (no data) counts as 0 in the sum
    if text == "":
        return 0.0
    return float(text)

with open("data/taco.csv", encoding="utf-8") as file:
    foods = list(csv.DictReader(file))

for food in foods:
    if food["kcal"] == "":
        continue

    kcal = to_number(food["kcal"])
    protein = to_number(food["protein"])
    carbs = to_number(food["carbs"])
    fat = to_number(food["fat"])

    expected = protein * 4 + carbs * 4 + fat * 9
    difference = abs(kcal - expected)
    
    if difference > 10 and difference / kcal > 0.15:
        print(f"{food['id']} {food['food']}: table {kcal} kcal, calculated {expected:.1f} kcal")
