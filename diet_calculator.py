# === TEST MODE ===
#True = uses fixed test values (no typing)
#False = asks the user (normal program)
TEST_MODE = False

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


def ask_number(prompt, number_type):
    # keep asking until the user types a valid number greater than 0
    while True:
        try:
            text = input(prompt).replace(",", ".")
            number = number_type(text)
            if number <= 0:
                print("Invalid! Please type a number greater than 0")
            else:
                return number
        except ValueError:
            print("Invalid! Please type a valid value")


if TEST_MODE:
    #fixed values just for testing
    age = 21
    weight = 72.0
    height = 173.0
    sex = "male"
    activity = 3

else:
    # real program: asks the user
    age = ask_number("Enter your age: ", int)
    weight = ask_number("Enter your weight in kg: ", float)
    height = ask_number("Enter your height in cm: ", float)

    while True:
        sex = input("Enter your sex (male/female): ").lower()
        if sex in BMR_COEFFICIENTS:
            break
        print("Invalid! Please type a valid value (e.g. male or female)")

    print("Activity level:")
    print("0 - Not used")
    print("1 - Sedentary (little or no exercise)")
    print("2 - Light (1-3 days/week)")
    print("3 - Moderate (3-5 days/week)")
    print("4 - Intense (6-7 days/week)")
    print("5 - Very intense (twice a day or heavy physical work)")

    while True:
        try:
            activity = int(input("Enter your activity level: "))
            if activity > 5 or activity < 0:
                print("Invalid! Please enter a value between 0 - 5")
            else:
                break
        except ValueError:
            print("Invalid! Please enter a valid value (e.g. 3)")


activity_factor = ACTIVITY_FACTORS[activity]
bmi = calculate_bmi(weight, height)
bmr = calculate_bmr(sex, weight, height, age)
tdee = calculate_tdee(bmr, activity_factor)

#show data
print(f"Age: {age} | Weight: {weight} kg | Height: {height} cm | Sex: {sex} | Activity: {activity} | Factor: {activity_factor}")
print(f"BMI: {bmi:.2f}")
print(f"BMR: {bmr:.0f} kcal/day")
print(f"TDEE: {tdee:.0f} kcal/day")


