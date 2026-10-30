from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from food_search import load_index, search_foods
from meal_plan import MODEL, load_foods, substitute

foods = load_foods()
index = load_index()


@tool
def search_food(query: str) -> str:
    """Searches the TACO table for foods that match a description (e.g. "pãozinho").
    Returns up to 8 candidates with their id and values per 100 g."""
    lines = []
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


SYSTEM_PROMPT = """You are a diet assistant for a Brazilian user.
Always use search_food to find foods in the TACO table, and substitute_food for any calculation.
Never calculate nutrition values by yourself.
If none of the candidates matches what the user meant, say the food is not in the TACO table.
One French bread (pão francês / pãozinho) weighs 50 g.
Answer in Portuguese."""

agent = create_agent(
    model=ChatGoogleGenerativeAI(model=MODEL),
    tools=[search_food, substitute_food],
    system_prompt=SYSTEM_PROMPT,
)

print("Diet assistant (type 'sair' to quit)")
messages = []
while True:
    question = input("\nVocê: ")
    if question.lower() == "sair":
        break
    messages.append({"role": "user", "content": question})
    result = agent.invoke({"messages": messages})
    messages = result["messages"]
    print(f"\nAssistente: {messages[-1].text}")
