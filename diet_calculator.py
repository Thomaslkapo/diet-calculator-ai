# === TEST MODE ===
#True = uses fixed test values (no typing)
#False = asks the user (normal program)
TEST_MODE = True

if TEST_MODE:
    #fixed values just for testing
    age = 22
    weight = 70.0
    height = 173.0
    sex = "male"

else:   
    # real program: asks the user
    age = int(input("Enter your age: "))
    weight = float(input("Enter your weight in kg: "))
    height = float(input("Enter your height in centimeters: "))
    sex = input("Enter your sex (male/female): ").lower()

#show data
print(f"Age: {age} | Weight: {weight} kg | Height: {height} cm | Sex: {sex}")
