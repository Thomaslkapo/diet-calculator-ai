import json

from pytest import approx

from diet_calculator import calculate_bmi, calculate_bmr, calculate_targets, calculate_tdee


def test_bmi():
    # 72 kg, 1.73 m → 72 / 1.73²
    assert calculate_bmi(72, 173) == approx(24.06, abs=0.01)


def test_bmr_matches_webdiet():
    # same case checked on WebDiet: man, 21 years, 72 kg, 173 cm
    assert calculate_bmr("male", 72, 173, 21) == approx(1764, abs=1)


def test_tdee():
    assert calculate_tdee(1764, 1.55) == approx(2734, abs=1)


def test_targets_from_example_profile():
    with open("profile.example.json", encoding="utf-8") as file:
        profile = json.load(file)
    assert calculate_targets(profile) == {"kcal": 2187, "protein": 144, "carbs": 241, "fat": 72}
