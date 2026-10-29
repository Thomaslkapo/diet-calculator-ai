# 🥗 AI Diet Calculator

A personal Python project that calculates daily energy expenditure and macronutrient targets and, in the future, will suggest diet plans using AI grounded in a reliable nutrition database.

> 🚧 **Work in progress** — I'm learning Python and building this project step by step.

## 💡 Motivation

To plan my diet, I always had to open WebDiet to calculate my BMI, basal metabolic rate and daily calorie needs. I realized all of this is based on well-known mathematical formulas, so I decided to rebuild that logic from scratch in Python — as a way to practice programming and to create something I actually use in my daily life.

## 🎯 Goals

1. Automatically calculate energy expenditure from a person's basic information.
2. Use AI to suggest diets that hit the desired macronutrients, respecting personal food preferences and based on a validated nutrition table (TBCA) — not on data made up by the AI.

## ▶️ How to run

Requirements: [Python 3](https://www.python.org/downloads/) installed.

```bash
git clone https://github.com/Thomaslkapo/diet-calculator-ai.git
cd diet-calculator-ai
python diet_calculator.py
```

> 💡 The file has a `TEST_MODE` switch at the top:
> - `TEST_MODE = True` → runs with fixed sample values (no typing needed)
> - `TEST_MODE = False` → asks for your data in the terminal

## 🗺️ Roadmap

### Phase 1 – Calculator ✅ *(done)*
- [x] User input: age, weight (kg), height (cm) and sex
- [x] Physical activity level
- [x] BMI calculation
- [x] Basal Metabolic Rate (BMR) — Harris-Benedict equation (1984 revision, matches WebDiet)
- [x] Total Daily Energy Expenditure (TDEE = BMR × activity factor)
- [x] Input validation

### Phase 2 – Macronutrients ✅ *(done)*
- [x] Calorie deficit (%) applied over the TDEE
- [x] Protein and fat goals in grams per kg of body weight
- [x] Carbohydrates calculated from the remaining calories
- [x] Warning when protein and fat exceed the target calories

**Coming next:**
- [ ] Option to split macros by percentage
- [ ] Low/high carb days (carb cycling)

### Phase 3 – AI Assistant
- [ ] Use TBCA (Brazilian Food Composition Table) as the knowledge base
- [ ] AI that looks up foods in the table before answering (RAG)
- [ ] Meal plan suggestions based on the user's macros and food preferences

### Phase 4 – API & Deployment
- [ ] REST API with FastAPI
- [ ] Web interface, deployed online for anyone to try

## 🛠️ Tech Stack

- **Current:** Python
- **Planned:** LangChain, Hugging Face (embeddings), FastAPI

## 📐 Formulas

| Calculation | Formula |
|---|---|
| BMI (Body Mass Index) | weight (kg) ÷ height (m)² |
| BMR (Basal Metabolic Rate) | Harris-Benedict, revised by Roza & Shizgal (1984) |
| TDEE (Total Daily Energy Expenditure) | BMR × activity factor |
| Target calories | TDEE × (1 − deficit % ÷ 100) |
| Protein / Fat (g) | body weight (kg) × g/kg goal |
| Carbohydrates (g) | (target calories − protein kcal − fat kcal) ÷ 4 |

> Energy per gram: protein 4 kcal · carbohydrates 4 kcal · fat 9 kcal

## 📚 References

- Harris, J. A.; Benedict, F. G. (1918). *A Biometric Study of Human Basal Metabolism.*
- Roza, A. M.; Shizgal, H. M. (1984). *The Harris Benedict equation reevaluated.* (revised version)
- [TBCA – Brazilian Food Composition Table](https://www.tbca.net.br/)

## ⚠️ Disclaimer

This is a study project. Results are estimates and do not replace guidance from a nutritionist or physician.

## 👤 Author

**Thomas Tellez**
Systems Analysis and Development student
[LinkedIn](https://linkedin.com/in/thomastellez) · [GitHub](https://github.com/Thomaslkapo)
