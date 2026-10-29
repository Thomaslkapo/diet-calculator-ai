import truststore
from dotenv import load_dotenv
from google import genai

# use Windows' trusted certificates (needed when an antivirus inspects HTTPS)
truststore.inject_into_ssl()

# reads the .env file and loads GEMINI_API_KEY
load_dotenv()

# the client finds GEMINI_API_KEY by itself

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents="Say hello to Thomas in Portuguese, in one short sentence",
)

print(response.text)