import truststore
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

INDEX_FOLDER = "data/food_index"

# use Windows' trusted certificates (needed when an antivirus inspects HTTPS)
truststore.inject_into_ssl()
# reads the .env file and loads GEMINI_API_KEY
load_dotenv()


def load_index():
    # opens the index saved by scripts/build_index.py (must use the same embedding model)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    return FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)


def search_foods(index, query, k=8):
    # returns the k foods whose meaning is closest to the query, as (id, name) pairs
    results = index.similarity_search(query, k=k)
    return [(doc.metadata["id"], doc.page_content) for doc in results]


if __name__ == "__main__":
    index = load_index()
    for query in ["pãozinho", "frango cozido", "queijo mussarela"]:
        print(query)
        for food_id, name in search_foods(index, query):
            print(f"  {food_id} {name}")
