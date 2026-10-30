# 🥗 AI Diet Calculator

A Python project that calculates energy expenditure and macronutrient targets, and includes an **AI diet assistant** that answers food substitution questions in plain Portuguese, using **RAG** over the official Brazilian food composition table (TACO) and **exact calculations done in Python**.

> 🚧 **Work in progress** — I'm learning Python and building this project step by step.

## 💡 Motivation

I follow a diet with fixed macros, and in my day-to-day life the same problem kept coming up: **I don't have a certain food at home, or I skipped part of a meal, and I need to know how much of something else to eat instead.** How much rice replaces two French breads? How much banana replaces 200 g of rice? How many eggs replace the cheese?

Answering that meant looking up both foods in a nutrition table and doing the macro math by hand — every single time. It took time, and it was easy to get wrong.

So I built an assistant that does it for me: I ask the question the way I would ask a person, and it finds the foods in a reliable table and calculates the exact amount.

It started as a rebuild of the calculations I used to do on WebDiet (BMI, basal metabolic rate, daily calories and macros) and grew into an AI project I actually use every day.

## 💬 Demo

```
$ python assistant.py
Diet assistant (type 'sair' to quit)

Você: não comi 2 pãezinhos hoje, quanto de arroz posso comer no lugar?

Assistente: Dois pãezinhos franceses (50 g cada) somam 100 g de pão. Para ter
a mesma quantidade de carboidratos, você pode comer cerca de 209 g de arroz
branco cozido (tipo 1).

Você: e se fosse banana?

Assistente: Você pode comer cerca de 225 g de banana prata.
```

Behind the scenes, the AI searched the TACO table for "pão francês" and "arroz cozido", picked the right foods, and called a Python function to calculate the grams. **The AI never does the math.**

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
        └──► substitute_food  exact macro math in Python, with TACO values
                              100 g French bread = 209 g rice (same carbs)
        │
        ▼
AI answers using the tool results
```

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

Then:

```bash
python assistant.py          # AI diet assistant (food substitutions)
python diet_calculator.py    # BMI, BMR, TDEE and macro targets
python food_search.py        # try the semantic food search
```

> 💡 `diet_calculator.py` has a `TEST_MODE` switch at the top: `True` runs with fixed sample values, `False` asks for your data in the terminal.

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
- [ ] Raw ↔ cooked weight conversion as a dedicated tool
- [ ] Meal plan building as an agent tool, with Python adjusting portions to hit the targets
- [ ] Connect the assistant to the user's own macro targets from the calculator

### Phase 4 – API & Deployment
- [ ] REST API with FastAPI
- [ ] Web interface, deployed online for anyone to try

## 🛠️ Tech Stack

- **Language:** Python
- **AI:** Google Gemini (chat model and embeddings, free tier)
- **Framework:** LangChain (agent, tools, vector store integration)
- **Vector store:** FAISS
- **Data:** TACO table — xlrd (reading the official spreadsheet), csv
- **Planned:** FastAPI

## 📁 Project Structure

```
diet-calculator-ai/
├── assistant.py               # AI diet assistant: LangChain agent with search + substitution tools
├── food_search.py             # RAG retrieval: semantic search over TACO foods
├── meal_plan.py               # food lookup, portion macros, plan totals, substitution, AI meal plan
├── diet_calculator.py         # BMI, BMR, TDEE and macro targets
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
