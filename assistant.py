from typing import Literal

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from diet_calculator import calculate_targets, load_profile
from food_search import load_index, search_foods
from meal_plan import (
    MODEL, fill_with_food, fit_macros, fit_with_fill, load_foods, plan_totals, scale_plan, substitute, to_number,
)

foods = load_foods()
index = load_index()

try:
    # your real targets, from the data saved by diet_calculator.py
    TARGETS = calculate_targets(load_profile())
except FileNotFoundError:
    print("profile.json not found: run diet_calculator.py first and save your data.")
    raise SystemExit


@tool
def search_food(queries: list[str]) -> str:
    """Searches the TACO table for every food in the list at once (e.g. ["pãozinho", "frango cozido"]).
    Returns up to 8 candidates per food, with their id and values per 100 g."""
    lines = []
    for query in queries:
        lines.append(f"Results for '{query}':")
        for food_id, name in search_foods(index, query):
            food = foods[food_id]
            lines.append(
                f"id {food_id}: {food['food']} | per 100 g: {food['kcal']} kcal, "
                f"protein {food['protein']} g, carbs {food['carbs']} g, fat {food['fat']} g"
            )
    return "\n".join(lines)


@tool
def substitute_food(old_food_id: str, old_grams: float, new_food_id: str, macro: str) -> str:
    """Calculates how many grams of the new food give the same amount of a macro
    ("carbs", "protein" or "fat") as the old food."""
    grams = substitute(foods, old_food_id, old_grams, new_food_id, macro)
    if grams is None:
        return f"{foods[new_food_id]['food']} has no {macro}, so it cannot replace it."
    return f"{grams:.0f} g of {foods[new_food_id]['food']} replaces {old_grams:.0f} g of {foods[old_food_id]['food']} ({macro})"


class PlanItem(BaseModel):
    meal: str = Field(description="meal name, e.g. breakfast, lunch, snack, dinner")
    food_id: str = Field(description="TACO food id returned by search_food")
    grams: float = Field(description="amount the user asked for, or a normal portion")
    fixed: bool = Field(default=False, description="true only when the user wants exactly this amount")


@tool
def build_plan(
    items: list[PlanItem],
    mode: Literal["macros", "fill_carbs", "fill_fat", "fill_food", "calories"],
    fill_food_id: str = "",
) -> str:
    """Adjusts the grams of a one-day meal plan to the user's targets, with exact math.
    mode: "macros" hits protein, carbs and fat;
    "fill_carbs" or "fill_fat" hits protein and calories, completing what is missing with carbs or fat;
    "fill_food" keeps every amount and puts all the missing calories in one food (fill_food_id, which must be in items);
    "calories" only hits the calories."""
    plan = [{"meal": item.meal, "id": item.food_id, "grams": item.grams, "fixed": item.fixed} for item in items]
    for item in plan:
        if item["id"] not in foods:
            return f"id {item['id']} does not exist, use search_food to find the right id."

    if mode != "fill_food" and all(item["fixed"] for item in plan):
        # with every food fixed, nothing can be adjusted
        return "every food is fixed, so nothing can change: set fixed false on the foods that can change and call build_plan again."

    if mode == "fill_food":
        if fill_food_id not in [item["id"] for item in plan]:
            return "fill_food_id must be the id of one of the items in the plan."
        if to_number(foods[fill_food_id]["kcal"]) == 0:
            return f"{foods[fill_food_id]['food']} has no calories, so it cannot fill the plan."
        adjusted = fill_with_food(plan, foods, TARGETS["kcal"], fill_food_id)
    elif mode == "calories":
        adjusted = scale_plan(plan, foods, TARGETS["kcal"])
    elif mode == "fill_carbs":
        adjusted = fit_with_fill(plan, foods, TARGETS, "carbs")
    elif mode == "fill_fat":
        adjusted = fit_with_fill(plan, foods, TARGETS, "fat")
    else:
        adjusted = fit_macros(plan, foods, TARGETS)

    lines = []
    for item in adjusted:
        lines.append(f"{item['meal']}: {item['grams']} g {foods[item['id']]['food']}")
    totals = plan_totals(adjusted, foods)
    for key in TARGETS:
        lines.append(f"{key}: {totals[key]:.0f} / {TARGETS[key]} (difference {totals[key] - TARGETS[key]:+.0f})")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are a diet assistant for a Brazilian user.
Always use search_food to find foods in the TACO table, and the other tools for any calculation.
Never calculate nutrition values by yourself.
Call search_food only once per question, with every food you need in the list.
To build a meal plan: find every food with search_food, then call build_plan once with all of them.
Choose the build_plan mode from what the user says:
- "fill_carbs" when they ask to complete what is missing with carbs (e.g. "completa com carbo")
- "fill_fat" when they ask to complete what is missing with fat (e.g. "completa com gordura")
- "fill_food" when they ask to put the missing calories in one specific food
  (e.g. "o resto das kcal coloca em pão francês"); set fill_food_id to that food's id
  and use the amounts the user gave (or normal portions) for every other food
Use "fill_food" only when the user names one specific food to receive the rest;
"completa com carbo" names a macro, not a food, so it is always "fill_carbs" (and "completa com gordura" is "fill_fat").
- "calories" when they only care about calories (e.g. "só as calorias")
- "macros" in any other case
Amounts the user mentions (e.g. "2 pãezinhos") are only a starting point that build_plan may adjust.
Set fixed to true only for the specific food the user wants in that exact amount
(e.g. "quero comer exatamente 150 g de frango", "exatamente 2 pães", "150 g de frango, não mexe");
every other food stays with fixed false, even if the user gave an amount for it.
In fill_food mode the other foods already keep their amounts: leave fixed false.
When the user asks for a new version of a plan, start with fixed false for every food;
only fix the foods the user says "exatamente" about in that new request.
Show the plan and the totals exactly as build_plan returns them.
If a macro is far from its target, tell the user and suggest a food rich in that macro.
If none of the candidates matches what the user meant, say the food is not in the TACO table.
One French bread (pão francês / pãozinho) weighs 50 g.
Answer in Portuguese."""

agent = create_agent(
    model=ChatGoogleGenerativeAI(model=MODEL),
    tools=[search_food, substitute_food, build_plan],
    system_prompt=SYSTEM_PROMPT,
)

print("Diet assistant (type 'sair' to quit)")
print(f"Your targets: {TARGETS['kcal']} kcal | protein {TARGETS['protein']} g | carbs {TARGETS['carbs']} g | fat {TARGETS['fat']} g")
messages = []
while True:
    question = input("\nVocê: ")
    if question.lower() == "sair":
        break
    messages.append({"role": "user", "content": question})
    try:
        result = agent.invoke({"messages": messages})
    except Exception as error:
        # the question failed: take it out of the history so the conversation goes on clean
        messages.pop()
        if "RESOURCE_EXHAUSTED" in str(error):
            print("\nAssistente: limite grátis do Gemini atingido. Espere 1 minuto e mande de novo.")
        else:
            print(f"\nAssistente: erro ao falar com o Gemini ({type(error).__name__}). Tente de novo.")
        continue
    messages = result["messages"]
    print(f"\nAssistente: {messages[-1].text}")
