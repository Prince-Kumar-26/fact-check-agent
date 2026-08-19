import pytest
import asyncio
import httpx
import json

# Define our Ground Truth dataset
# We want to test a mix of True, False, and Unverifiable claims.
GROUND_TRUTH = [
    {
        "claim": "The Earth orbits the Sun.",
        "expected_verdict": "True",
        "category": "Science"
    },
    {
        "claim": "Vaccines alter your DNA.",
        "expected_verdict": "False",
        "category": "Health"
    },
    {
        "claim": "Water boils at 100 degrees Celsius at sea level.",
        "expected_verdict": "True",
        "category": "Science"
    },
    {
        "claim": "Humans only use 10 percent of their brains.",
        "expected_verdict": "False",
        "category": "Science/Health"
    },
    {
        "claim": "The moon is made entirely of cheese.",
        "expected_verdict": "False",
        "category": "Science"
    }
]

API_URL = "http://localhost:8000/api/factcheck"

@pytest.mark.asyncio
async def test_evaluate_fact_check_engine():
    """
    Automated Evaluation Suite:
    Iterates through the ground truth dataset and asserts the AI Judge's verdict matches reality.
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        correct_predictions = 0
        total = len(GROUND_TRUTH)
        
        print("\n--- Starting Automated Evaluations ---")
        
        for idx, test_case in enumerate(GROUND_TRUTH):
            print(f"[{idx+1}/{total}] Evaluating Claim: {test_case['claim']}")
            
            response = await client.post(API_URL, json={"claim": test_case['claim']})
            assert response.status_code == 200, f"API returned status {response.status_code}"
            
            data = response.json()
            
            # The system might reject invalid claims (like politics), but our ground truth should be valid
            assert data.get("status") == "COMPLETED", f"Claim was rejected: {data.get('rejection_reason')}"
            
            actual_verdict = data.get("verdict")
            expected_verdict = test_case["expected_verdict"]
            
            print(f"  -> Expected: {expected_verdict} | Actual: {actual_verdict}")
            
            if actual_verdict == expected_verdict:
                correct_predictions += 1
            else:
                print(f"  [X] MISMATCH! The AI Judge got this wrong.")
                
        # Calculate accuracy metric
        accuracy = (correct_predictions / total) * 100
        print(f"\n--- Evaluation Complete ---")
        print(f"Final Accuracy: {accuracy}% ({correct_predictions}/{total})")
        
        # We enforce a high threshold for a production engine
        assert accuracy >= 80.0, f"Engine accuracy fell below 80% threshold (Current: {accuracy}%)"
