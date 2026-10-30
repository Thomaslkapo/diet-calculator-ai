# 🥗 AI Diet Calculator

A Python project that calculates energy expenditure and macronutrient targets, and includes an **AI diet assistant** that answers food substitution questions and builds meal plans in plain Portuguese, using **RAG** over the official Brazilian food composition table (TACO) and **exact calculations done in Python**.

> 🚧 **Work in progress** — I'm learning Python and building this project step by step.

## 💡 Motivation

I follow a diet with fixed macros, and in my day-to-day life the same problem kept coming up: **I don't have a certain food at home, or I skipped part of a meal, and I need to know how much of something else to eat instead.** How much rice replaces two French breads? How much banana replaces 200 g of rice? How many eggs replace the cheese?

Answering that meant looking up both foods in a nutrition table and doing the macro math by hand — every single time. It took time, and it was easy to get wrong.

So I built an assistant that does it for me: I ask the question the way I would ask a person, and it finds the foods in a reliable table and calculates the exact amount. It also builds a full day of meals from the foods I choose, adjusting the grams until the plan hits my targets.

It started as a rebuild of the calculations I used to do on WebDiet (BMI, basal metabolic rate, daily calories and macros) and grew into an AI project I actually use every day.

## 💬 Demo

```
$ python assistant.py
Diet assistant (type 'sair' to quit)
Your targets: 2187 kcal | protein 144 g | carbs 241 g | fat 72 g

Você: não comi 2 pãezinhos hoje, quanto de arroz posso comer no lugar?

Assistente: Dois pãezinhos franceses (50 g cada) somam 100 g de pão. Para ter
a mesma quantidade de carboidratos, você pode comer cerca de 209 g de arroz
branco cozido (tipo 1).

Você: e se fosse banana?

Assistente: Você pode comer cerca de 225 g de banana prata.

Você: café 2 pães, almoço 150 g arroz e 200 g frango cru, jantar 2 ovos cozidos,
completa com carbo

Assistente:
café: 292 g Pão, trigo, francês
almoço: 437 g Arroz, tipo 1, cozido
almoço: 387 g Frango, peito, sem pele, cru
jantar: 200 g Ovo, de galinha, inteiro, cozido
kcal: 2189 / 2187 | protein: 144 / 144 | carbs: 295 / 241 | fat: 41 / 72
A gordura ficou abaixo da meta, então os carboidratos completaram as calorias.
Para chegar perto dos 72 g, inclua uma fonte de gordura, como azeite.
```

Behind the scenes, the AI searched the TACO table for every food in one call, picked the right ones, and called Python functions to calculate the grams. **The AI never does the math.**

## 🧠 How it works

```
You ask in Portuguese
        │
        ▼
AI agent (Gemini + LangChain, ReAct pattern)
  decides which tools to call
        │
        ├──► search_food      RAG: semantic search over the 597 TACO foods
        │                     (Gemini embeddings + FAISS vector store)
        │                     "pãozinho" → Pão, trigo, francês
        │
        ├──► substitute_food  exact macro math in Python, with TACO values
        │                     100 g French bread = 209 g rice (same carbs)
        │
        └──► build_plan       adjusts the grams of a full day of meals
                              to the user's targets (see below)
        │
        ▼
AI answers using the tool results
```

### Building a meal plan

The user chooses the foods; the AI finds them in the table and picks a **mode** from the way the user asks; Python adjusts the grams:

| The user says | Mode | What Python does |
|---|---|---|
| *(nothing special)* | `macros` | hits protein, carbs and fat |
| "completa com carbo" / "completa com gordura" | `fill_carbs` / `fill_fat` | hits protein and calories; what the foods can't give in the other macros is completed with carbs (or fat) |
| "o resto das kcal coloca em pão" | `fill_food` | keeps every amount and puts all the missing calories in that one food |
| "só as calorias" | `calories` | scales every portion by the same factor |

How the adjustment works (`fit_macros` in `meal_plan.py`):
- Each food joins the group of its **main macro** (the one that gives it the most calories): chicken → protein, rice → carbs, egg → fat.
- Group by group (protein → fat → carbs), all portions in the group are multiplied by the factor that makes that macro hit its target. Since foods have more than one macro, the loop repeats until every group settles (it usually converges in about 5 rounds).
- **Portion limits:** a portion stays between **0.5× and 2×** of its starting amount, so the plan never turns into 600 g of eggs. In the fill modes, the group that fills the plan (carbs or fat) can grow past 2×, because the user asked for it.
- **Fixed foods:** "quero comer exatamente 150 g de frango" locks that food; Python never changes it.
- Low-calorie foods (under 50 kcal per 100 g, like vegetables) keep their portion.
- Grams are rounded to whole numbers — the precision of a kitchen scale.

### Reliability

- **Fewer requests:** `search_food` takes a list, so the AI looks up every food of a plan in a single tool call (batching) instead of one call per food. That cuts the requests to the model by about half per question, which matters on the free tier's limit of 15 requests per minute.
- **Errors don't end the conversation:** if the API fails (rate limit `429`, server overload), the assistant explains it and the chat goes on.
- **Tools check the AI's input:** an id that doesn't exist, a fill food that isn't in the plan, or a plan where every food is locked returns a message to the AI, which fixes the call by itself.
- **Exact choices with `Literal`:** the mode argument only accepts the listed values, so the model can't invent a new one.

**Why the AI doesn't do the math:** language models are good at understanding requests and choosing foods, but they are not calculators. In an early experiment, I asked the AI to build a full-day meal plan for a 2187 kcal target: the plan it returned added up to **3407 kcal** when Python checked it against the TACO values. So the project splits the work:

| Part | Who does it |
|---|---|
| Understanding the question, choosing foods | AI (Gemini) |
| Finding foods in the table, even with informal names | RAG (embeddings + FAISS) |
| Every number (grams, macros, calories) | Python, with official TACO data |

**Why RAG:** TACO names foods formally ("Pão, trigo, francês"), but people don't talk like that ("pãozinho"). A keyword search finds nothing; a semantic search with embeddings finds the right food by meaning — "pãozinho" returns French bread as the top result, and "queijo branco" returns minas frescal cheese.

## ▶️ How to run

Requirements: **Python 3.13** (some AI packages don't support newer versions yet) and a free **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/Thomaslkapo/diet-calculator-ai.git
cd diet-calculator-ai
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

Create a `.env` file in the project folder with your key (it is in `.gitignore`, so it never goes to GitHub):

```
GEMINI_API_KEY=your_key_here
```

Then calculate your targets and save your data (age, weight, height, activity, deficit and protein/fat goals) — answer `yes` at the end:

```bash
python diet_calculator.py    # BMI, BMR, TDEE and macro targets → saves profile.json
python assistant.py          # AI diet assistant (substitutions and meal plans)
python food_search.py        # try the semantic food search
```

The assistant reads `profile.json` and calculates your targets every time it starts. Your data stays on your computer: `profile.json` is in `.gitignore`. To try the assistant with sample data, copy `profile.example.json` to `profile.json`.

> 💡 `diet_calculator.py` has a `TEST_MODE` switch at the top: `True` runs with fixed sample values (and doesn't save a profile), `False` asks for your data in the terminal.

Run the automated tests (they check every calculation, with no API calls):

```bash
pytest
```

The search index (`data/food_index/`) is already included. To rebuild the data from scratch (optional):

```bash
python scripts/convert_taco.py     # official spreadsheet → data/taco.csv
python scripts/validate_taco.py    # checks calories against macronutrients
python scripts/build_index.py      # creates the embeddings index (~7 min on the free tier)
```

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

### Phase 3 – AI Diet Assistant 🚧 *(in progress)*
- [x] Convert the official TACO table into a clean CSV (597 foods)
- [x] Validate the converted data (calories vs. macronutrients)
- [x] Connection to an AI model (API key kept out of the repository)
- [x] Python verification of AI-generated meal plans against macro targets
- [x] Food substitution by macronutrient (exact calculation in Python)
- [x] RAG: semantic food search with embeddings and a FAISS vector store
- [x] AI agent (LangChain, ReAct) that uses search and substitution as tools
- [x] Meal plan building as an agent tool, with Python adjusting portions to hit the targets
- [x] Plan modes: every macro, fill with carbs or fat, fill with a chosen food, calories only
- [x] Portion limits and fixed foods
- [x] Connect the assistant to the user's own targets (saved profile, kept out of the repository)
- [x] Batched food search and API error handling
- [ ] Raw ↔ cooked weight conversion as a dedicated tool
- [ ] Update the profile by chatting ("agora estou com 70 kg")

### Phase 4 – API & Deployment
- [ ] REST API with FastAPI
- [ ] Web interface, deployed online for anyone to try

## 🛠️ Tech Stack

- **Language:** Python
- **AI:** Google Gemini (chat model and embeddings, free tier)
- **Framework:** LangChain (agent, tools, vector store integration)
- **Tests:** pytest
- **Vector store:** FAISS
- **Data:** TACO table — xlrd (reading the official spreadsheet), csv
- **Planned:** FastAPI

## 📁 Project Structure

```
diet-calculator-ai/
├── assistant.py               # AI diet assistant: LangChain agent with search, substitution and meal plan tools
├── food_search.py             # RAG retrieval: semantic search over TACO foods
├── meal_plan.py               # portion macros, plan totals, substitution, portion fitting (fit_macros, fill modes)
├── diet_calculator.py         # BMI, BMR, TDEE and macro targets; saves/loads the user's profile
├── profile.example.json       # sample profile (your own profile.json stays out of Git)
├── data/
│   ├── raw/
│   │   └── taco_4a_edicao_2011.xls   # official TACO spreadsheet (unchanged)
│   ├── taco.csv               # clean table generated by convert_taco.py
│   └── food_index/            # FAISS index with the embeddings of every food
├── scripts/
│   ├── explore_taco.py        # prints the first rows to inspect the spreadsheet layout
│   ├── convert_taco.py        # spreadsheet → data/taco.csv
│   ├── validate_taco.py       # checks calories against macronutrients
│   ├── build_index.py         # builds data/food_index with Gemini embeddings
│   └── hello_ai.py            # first connection test with the Gemini API
├── tests/
│   ├── test_diet_calculator.py   # BMI, BMR, TDEE and targets (WebDiet reference case)
│   └── test_meal_plan.py         # substitution, portion fitting, limits, fixed foods, fill modes
├── pytest.ini
└── requirements.txt
```

## 📊 Data

Food data comes from **TACO** (Tabela Brasileira de Composição de Alimentos, 4th edition), published by NEPA/UNICAMP — a reliable public reference for Brazilian foods.

**Conversion** (`scripts/convert_taco.py`): reads the official spreadsheet and keeps only the columns the project needs — food, category, kcal, protein, fat, carbohydrates and fiber (all per 100 g).
- `Tr` (trace, too small to measure) → `0`
- `NA` (not applicable) and `*` (under review) → empty, so missing data is never mistaken for zero

**Validation** (`scripts/validate_taco.py`): for every food, compares the table's calories with the value calculated from its macros (protein × 4 + carbs × 4 + fat × 9) and lists the foods that differ by more than 10 kcal **and** 15%.
Result: only 14 of 597 foods are flagged, all explained by TACO itself (alcoholic drinks, whose alcohol calories are not part of the formula, and foods calculated with specific conversion factors) — not by conversion errors.

**Search index** (`scripts/build_index.py`): each food name and category (e.g. "Pão, trigo, francês (Cereais e derivados)") is turned into an embedding with Gemini (`gemini-embedding-2`) and stored in a FAISS index. Searches return the closest foods by Euclidean distance.

> Carbohydrate values in TACO are total carbohydrates (fiber included).

## 📐 Formulas

| Calculation | Formula |
|---|---|
| BMI (Body Mass Index) | weight (kg) ÷ height (m)² |
| BMR (Basal Metabolic Rate) | Harris-Benedict, revised by Roza & Shizgal (1984) |
| TDEE (Total Daily Energy Expenditure) | BMR × activity factor |
| Target calories | TDEE × (1 − deficit % ÷ 100) |
| Protein / Fat (g) | body weight (kg) × g/kg goal |
| Carbohydrates (g) | (target calories − protein kcal − fat kcal) ÷ 4 |
| Macros of a portion | value per 100 g × grams ÷ 100 |
| Substitution (g of new food) | macro in the old portion ÷ macro per 100 g of the new food × 100 |
| Group factor (fit_macros) | (macro target − macro from the other foods) ÷ macro from the group |
| Fill food (g) | (target calories − calories of the other foods) ÷ kcal per 100 g × 100 |

> Energy per gram: protein 4 kcal · carbohydrates 4 kcal · fat 9 kcal

**Substitution example:** 100 g of French bread has 58.6 g of carbs. Rice has 28.1 g of carbs per 100 g, so 58.6 ÷ 28.1 × 100 = **209 g of rice**.

## 📚 References

- Harris, J. A.; Benedict, F. G. (1918). *A Biometric Study of Human Basal Metabolism.*
- Roza, A. M.; Shizgal, H. M. (1984). *The Harris Benedict equation reevaluated.* (revised version)
- NEPA – Núcleo de Estudos e Pesquisas em Alimentação. *Tabela Brasileira de Composição de Alimentos – TACO.* 4th ed. Campinas: NEPA/UNICAMP, 2011.
- Spreadsheet file obtained from [raulfdm/taco-api](https://github.com/raulfdm/taco-api) (MIT License).

## ⚠️ Disclaimer

This is a study project. Results are estimates and do not replace guidance from a nutritionist or physician.

## 👤 Author

**Thomas Tellez**
Systems Analysis and Development student
[LinkedIn](https://linkedin.com/in/thomastellez) · [GitHub](https://github.com/Thomaslkapo)
