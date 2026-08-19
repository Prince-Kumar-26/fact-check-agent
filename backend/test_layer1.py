from backend.layer_extractor import process_layer1

test_cases = [
    # 1. Valid Science Claim
    "ISRO launched the Chandrayaan-3 mission in July 2023 and achieved a soft landing near the lunar south pole.",
    
    # 2. Valid Compound Health Claim
    "Ayushman Bharat covers secondary and tertiary care hospitalization up to 5 lakh rupees per family per year.",
    
    # 3. Political Rejection Test
    "Party X won the election because their economic policy is strictly superior to the opposition.",
    
    # 4. Medical Advice / Dosage Rejection Test
    "I have severe chest pain and fever, should I take 500mg paracetamol or visit the ER?",
    
    # 5. Subjective Opinion Rejection Test
    "Quantum computing is the most interesting field in modern physics."
]

def run_tests():
    print("\n================= RUNNING LAYER 1 TEST SUITE =================\n")
    for i, test_input in enumerate(test_cases, 1):
        print(f"Test Case #{i}: \"{test_input}\"")
        output = process_layer1(test_input)
        
        if output.is_valid:
            print("🟢 STATUS: IN-SCOPE & EXTRACTED")
            for c in output.claims:
                print(f"   ├─ ID: {c.claim_id} [{c.domain}]")
                print(f"   ├─ Claim: {c.claim_text}")
                if c.is_compound:
                    print(f"   └─ Sub-Claims: {c.sub_claims}")
        else:
            print("🔴 STATUS: REJECTED (GUARDRAIL TRIPPED)")
            print(f"   └─ Reason: {output.rejection_reason}")
        print("-" * 65)

if __name__ == "__main__":
    run_tests()