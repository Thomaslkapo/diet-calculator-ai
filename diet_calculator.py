import json

# === TEST MODE ===
#True = uses fixed test values (no typing)
#False = asks the user (normal program)
TEST_MODE = False

# your data, read by assistant.py (in .gitignore: it is personal data)
PROFILE_FILE = "profile.json"

ACTIVITY_FACTORS = {
    # activity level: factor
    # (based on weekly exercise frequency)
    0: 1.0,
    1: 1.2,
    2: 1.375,
    3: 1.55,
    4: 1.725,
    5: 1.9}

# Harris-Benedict revised (Roza & Shizgal, 1984)
BMR_COEFFICIENTS = {
    "male": {"base": 88.362, "weight": 13.397, "height": 4.799, "age": 5.677},
    "female": {"base": 447.593, "weight":9.247, "height": 3.098, "age": 4.330},
}

# calories per gram of each macronutrient
KCAL_PER_GRAM = {
    "protein": 4,
    "carbs": 4,
    "fat": 9,
}


def calculate_bmi(weight, height_cm):
    return weight / (height_cm / 100) ** 2


def calculate_bmr(sex, weight, height_cm, age):
    # get the coefficients for this sex (male or female)
    coef = BMR_COEFFICIENTS[sex]
    # Harris-Benedict formula
    bmr = (coef["base"] + coef["weight"] * weight + coef["height"] * height_cm - coef["age"] * age)
    return bmr


def calculate_tdee(bmr, activity_factor):
    tdee = bmr * activity_factor
    return tdee


def calculate_target_calories(tdee, deficit):
    target_calories = tdee * (1 - deficit / 100)
    return target_calories


def calculate_macro_grams(weight, grams_per_kg):
    return weight * grams_per_kg


def calculate_carbs(target_calories, protein_g, fat_g):
    # carbs get whatever calories are left after protein and fat
    protein_kcal = protein_g * KCAL_PER_GRAM["protein"]
    fat_kcal = fat_g * KCAL_PER_GRAM["fat"]
    remaining_kcal = target_calories - protein_kcal - fat_kcal
    return remaining_kcal / KCAL_PER_GRAM["carbs"]


def calculate_macros(weight, target_calories, protein_per_kg, fat_per_kg):
    # builds the full macro split using the small functions above
    protein_g = calculate_macro_grams(weight, protein_per_kg)
    fat_g = calculate_macro_grams(weight, fat_per_kg)
    carbs_g = calculate_carbs(target_calories, protein_g, fat_g)
    return {"protein": protein_g, "fat": fat_g, "carbs": carbs_g}


def calculate_targets(profile):
    # all the daily targets from the user's data, rounded to whole numbers
    bmr = calculate_bmr(profile["sex"], profile["weight"], profile["height"], profile["age"])
    tdee = calculate_tdee(bmr, ACTIVITY_FACTORS[profile["activity"]])
    target_calories = calculate_target_calories(tdee, profile["deficit"])
    macros = calculate_macros(profile["weight"], target_calories, profile["protein_per_kg"], profile["fat_per_kg"])
    return {
        "kcal": round(target_calories),
        "protein": round(macros["protein"]),
        "carbs": round(macros["carbs"]),
        "fat": round(macros["fat"]),
    }


def save_profile(profile):
    # writes the user's data to profile.json
    with open(PROFILE_FILE, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)


def load_profile():
    # reads the user's data from profile.json
    with open(PROFILE_FILE, encoding="utf-8") as file:
        return json.load(file)


def ask_number(prompt, number_type, min_value):
    # keep asking until the user types a valid number of at least min_value
    while True:
        try:
            text = input(prompt).replace(",", ".")
            number = number_type(text)
            if number < min_value:
                print(f"Invalid! Please type a number of at least {min_value}")
            else:
                return number
        except ValueError:
            print("Invalid! Please type a valid value")


def ask_option(prompt, options, option_type):
    # keep asking until the answer is one of the options
    while True:
        try:
            answer = option_type(input(prompt).lower())
            if answer in options:
                return answer
            print("Invalid! Please choose one of the options")
        except ValueError:
            print("Invalid! Please type a valid value")


if __name__ == "__main__":
    if TEST_MODE:
        #fixed values just for testing
        age = 21
        weight = 72.0
        height = 173.0
        sex = "male"
        activity = 3
        deficit = 20
        protein_per_kg = 2
        fat_per_kg = 1

    else:
        # real program: asks the user
        age = ask_number("Enter your age: ", int, 1)
        weight = ask_number("Enter your weight in kg: ", float, 1)
        height = ask_number("Enter your height in cm: ", float, 1)
        sex = ask_option("Enter your sex (male/female): ", BMR_COEFFICIENTS, str)
        print("Activity level:")
        print("0 - Not used")
        print("1 - Sedentary (little or no exercise)")
        print("2 - Light (1-3 days/week)")
        print("3 - Moderate (3-5 days/week)")
        print("4 - Intense (6-7 days/week)")
        print("5 - Very intense (twice a day or heavy physical work)")
        activity = ask_option("Enter your activity level: ", ACTIVITY_FACTORS, int)
        # 0 = keep current weight
        deficit = ask_number("Enter your calorie deficit (%): ", float, 0)
        protein_per_kg = ask_number("Enter your protein goal (g/kg): ", float, 0)
        fat_per_kg = ask_number("Enter your fat goal (g/kg): ", float, 0)

    activity_factor = ACTIVITY_FACTORS[activity]
    bmi = calculate_bmi(weight, height)
    bmr = calculate_bmr(sex, weight, height, age)
    tdee = calculate_tdee(bmr, activity_factor)
    target_calories = calculate_target_calories(tdee, deficit)
    macros = calculate_macros(weight, target_calories, protein_per_kg, fat_per_kg)

    #show data
    print(f"Age: {age} | Weight: {weight} kg | Height: {height} cm | Sex: {sex} | Activity: {activity} | Factor: {activity_factor}")
    print(f"BMI: {bmi:.2f}")
    print(f"BMR: {bmr:.0f} kcal/day")
    print(f"TDEE: {tdee:.0f} kcal/day")
    print(f"Target calories: {target_calories:.0f} kcal/day")
    # negative carbs = protein and fat alone go over the target calories
    if macros["carbs"] < 0:
        print("Warning! Protein and fat go over your target calories. Lower your protein or fat goal.")
    else:
        print(f"Protein: {macros['protein']:.0f} g | Fat: {macros['fat']:.0f} g | Carbs: {macros['carbs']:.0f} g")

    if not TEST_MODE:
        # saves the answers so assistant.py uses your real targets
        save = ask_option("Save your data for the assistant? (yes/no): ", ["yes", "no"], str)
        if save == "yes":
            save_profile({
                "age": age, "weight": weight, "height": height, "sex": sex, "activity": activity,
                "deficit": deficit, "protein_per_kg": protein_per_kg, "fat_per_kg": fat_per_kg,
            })
            print(f"Saved to {PROFILE_FILE}")
