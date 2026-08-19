import os
import httpx
from typing import Optional
from dotenv import load_dotenv
from backend.schemas import FactCheckLookupResult

load_dotenv()

GOOGLE_FACT_CHECK_API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")

def lookup_fact_check(claim_text: str) -> FactCheckLookupResult:
    """
    Sub-phase 3.1: Google Fact Check Tools API Lookup Node.
    Queries the API to see if a human fact-check already exists for this claim.
    """
    if not GOOGLE_FACT_CHECK_API_KEY or GOOGLE_FACT_CHECK_API_KEY == "your_google_fact_check_api_key_here":
        # Fallback if key is missing
        return FactCheckLookupResult(has_existing_fact_check=False)

    url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": claim_text,
        "key": GOOGLE_FACT_CHECK_API_KEY,
        "languageCode": "en"
    }

    try:
        response = httpx.get(url, params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            
            if claims:
                # Get the top claim
                top_claim = claims[0]
                reviews = top_claim.get("claimReview", [])
                
                if reviews:
                    top_review = reviews[0]
                    return FactCheckLookupResult(
                        has_existing_fact_check=True,
                        verdict=top_review.get("textualRating"),
                        reviewer=top_review.get("publisher", {}).get("name"),
                        url=top_review.get("url")
                    )
                    
        return FactCheckLookupResult(has_existing_fact_check=False)
        
    except Exception as e:
        print(f"Error querying Google Fact Check API: {e}")
        return FactCheckLookupResult(has_existing_fact_check=False)
