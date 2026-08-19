from dotenv import load_dotenv
import os
import requests

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    if 'data' in data:
        print("Available Models:")
        for model in data['data']:
            print(f"- {model['id']}")
    else:
        print("Error fetching models:", data)
except Exception as e:
    print("Exception:", e)
