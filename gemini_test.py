import os
from dotenv import load_dotenv
from google import genai
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
if not api_key:
 raise SystemExit("GEMINI_API_KEY is missing from .env")
try:
 client = genai.Client(api_key=api_key)
 result = client.interactions.create(
 model=model,
 input="Say: JalMitra AI connection is successful!"
 )
 print(result.output_text)
except Exception as error:
 print("Gemini connection failed:", error)