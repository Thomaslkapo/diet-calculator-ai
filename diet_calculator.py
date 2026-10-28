# === TEST MODE ===
#True = uses fixed test values (no typing)
#False = asks the user (normal program)
TEST_MODE = True

ACTIVITY_FACTORS = {
    # activity level: factor
    # (based on weekly exercise frequency)
    0: 1.0, 
    1: 1.2, 
    2: 1.375, 
    3: 1.55, 
    4: 1.725, 
    5: 1.9}

if TEST_MODE:
    #fixed values just for testing
    age = 22
    weight = 70.0
    height = 173.0
    sex = "male"
    activity = 3

else:   
    # real program: asks the user
    age = int(input("Enter your age: "))
    weight = float(input("Enter your weight in kg: "))
    height = float(input("Enter your height in centimeters: "))
    sex = input("Enter your sex (male/female): ").lower()
    print("Activity level:")
    print("0 - Not used")
    print("1 - Sedentary (little or no exercise)")
    print("2 - Light (1-3 days/week)")
    print("3 - Moderate (3-5 days/week)")
    print("4 - Intense (6-7 days/week)")
    print("5 - Very intense (twice a day or heavy physical work)")
    activity = int(input("Enter your activity level: "))

activity_factor = ACTIVITY_FACTORS[activity]

#show data
print(f"Age: {age} | Weight: {weight} kg | Height: {height} cm | Sex: {sex} | Activity: {activity} | Factor: {activity_factor}")
