from dotenv import load_dotenv
load_dotenv()
import os
from pydantic import BaseModel
from groq import Groq
import instructor

class Person(BaseModel):
    name: str
    age: int

client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
try:
    resp = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        response_model=Person,
        messages=[{"role": "user", "content": "Extract: Jason is 25 years old."}]
    )
    print("Success:", resp)
except Exception as e:
    print("Error:", e)
