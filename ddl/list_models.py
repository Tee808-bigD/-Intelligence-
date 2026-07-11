import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        print("Available models:")
        for model in client.models.list():
            print(f"- {model.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
