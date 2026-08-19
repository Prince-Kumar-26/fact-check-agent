import os
from pydantic import BaseModel, Field
from typing import List
from groq import Groq
import instructor
from dotenv import load_dotenv

load_dotenv()

class AtomicClaim(BaseModel):
    claim_id: int
    claim_text: str
    domain: str

class AtomicClaimList(BaseModel):
    claims: List[AtomicClaim]

client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")), mode=instructor.Mode.JSON)

try:
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=AtomicClaimList,
        messages=[{"role": "user", "content": "Extract: Water boils at 100 degrees Celsius."}]
    )
    print("Success JSON mode:", resp)
except Exception as e:
    print("Error JSON mode:", e)

client_tool = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
try:
    resp = client_tool.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=AtomicClaimList,
        messages=[{"role": "user", "content": "Extract: Water boils at 100 degrees Celsius."}]
    )
    print("Success Tool mode:", resp)
except Exception as e:
    print("Error Tool mode:", e)
