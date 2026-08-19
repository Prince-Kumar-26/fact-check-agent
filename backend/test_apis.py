import os
import httpx
from dotenv import load_dotenv
from groq import Groq
from google import genai
from tavily import TavilyClient

# 1. Load Environment Variables from the CURRENT directory
load_dotenv()

def test_groq():
    print("\n--- Testing Groq (Llama 3) ---")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "In one short sentence, say 'Groq is active!'" }],
            model="llama-3.3-70b-versatile", 
        )
        print(f"✅ Success: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Groq Error: {e}")

def test_gemini():
    print("\n--- Testing Google Gemini (Auto-Detect Mode) ---")
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Gemini Error: GEMINI_API_KEY not found in .env")
            return

        client = genai.Client(api_key=api_key)
        
        print("Fetching your permitted models from Google AI Studio...")
        # Fetch all models attached to your specific key
        available_models = client.models.list()
        
        working_model = None
        
        # Test each model until one works
        for m in available_models:
            model_name = m.name.replace("models/", "")
            
            # Skip embedding or vision-only models
            if "embed" in model_name or "vision" in model_name or "tts" in model_name:
                continue
                
            try:
                print(f"Attempting to connect via '{model_name}'...")
                chat = client.chats.create(model=model_name)
                response = chat.send_message("Say 'Active!'")
                
                if response.text:
                    print(f"✅ SUCCESS! Your account allows: '{model_name}'")
                    working_model = model_name
                    break # Stop as soon as we find a working one
                    
            except Exception:
                continue # If it 404s or fails, silently move to the next one
                
        if not working_model:
            print("❌ FATAL: None of the models attached to this API key allow text generation.")
            print("Action Required: You must generate a brand new API key directly from https://aistudio.google.com/app/apikey")
            
    except Exception as e:
        print(f"❌ Critical Gemini Error: {e}")

def test_tavily():
    print("\n--- Testing Tavily (Live Web Search) ---")
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search("What is the capital of India?", max_results=1)
        if response.get('results'):
            print(f"✅ Success: Found a search result. Title: '{response['results'][0]['title']}'")
        else:
            print("⚠️ Tavily worked, but returned no results.")
    except Exception as e:
        print(f"❌ Tavily Error: {e}")

def test_google_fact_check():
    print("\n--- Testing Google Fact Check Tools API ---")
    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
    if not api_key or api_key == "your_google_fact_check_api_key_here":
        print("⚠️ Google Fact Check API key not set or is still the default template. Skipping.")
        return
        
    try:
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query=moon&key={api_key}"
        response = httpx.get(url)
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            print(f"✅ Success: Retrieved {len(claims)} recent human fact-checks from the aggregator.")
        else:
            print(f"❌ Google API Error: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Google API Request Error: {e}")

if __name__ == "__main__":
    print("Starting API Verification Suite...")
    test_groq()
    test_gemini()
    test_tavily()
    test_google_fact_check()
    print("\n🎉 Phase 1.3 Complete: API Verification Finished!")