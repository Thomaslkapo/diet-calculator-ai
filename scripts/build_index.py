# Builds the RAG search index: turns every TACO food name into an embedding
# (numbers that represent its meaning) and saves them in a FAISS index.
#
# Run once from the project root (takes ~7 minutes on the free tier):
#   python scripts/build_index.py

import csv
import time

import truststore
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

TACO_FILE = "data/taco.csv"
INDEX_FOLDER = "data/food_index"
BATCH_SIZE = 90  # free tier allows 100 embeddings per minute

# use Windows' trusted certificates (needed when an antivirus inspects HTTPS)
truststore.inject_into_ssl()
# reads the .env file and loads GEMINI_API_KEY
load_dotenv()

# one document per food: the text that gets embedded + the food id
documents = []
with open(TACO_FILE, encoding="utf-8") as file:
    for row in csv.DictReader(file):
        text = f"{row['food']} ({row['category']})"
        documents.append(Document(page_content=text, metadata={"id": row["id"]}))

# the model that turns text into numbers (embeddings)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

index = None
for start in range(0, len(documents), BATCH_SIZE):
    batch = documents[start:start + BATCH_SIZE]
    if index is None:
        index = FAISS.from_documents(batch, embeddings)
    else:
        index.add_documents(batch)
    print(f"{start + len(batch)} / {len(documents)} foods indexed", flush=True)
    if start + BATCH_SIZE < len(documents):
        time.sleep(62)  # wait for the per-minute limit to reset

index.save_local(INDEX_FOLDER)
print(f"Index saved to {INDEX_FOLDER}")
