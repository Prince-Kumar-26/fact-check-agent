from backend.layer_extractor import process_layer1
from backend.fact_check_lookup import lookup_fact_check
from backend.retrieval_router import route_and_retrieve

test_claims = [
    "The moon landing in 1969 was faked by NASA in a Hollywood studio.",
    "mRNA COVID-19 vaccines can permanently alter your DNA."
]

def run_tests():
    print("\n================= RUNNING LAYER 2 TEST SUITE =================\n")
    for i, test_input in enumerate(test_claims, 1):
        print(f"Test Case #{i}: \"{test_input}\"")
        
        # --- LAYER 1 ---
        print("\n--- Running Layer 1 (Extraction) ---")
        layer1_output = process_layer1(test_input)
        if not layer1_output.is_valid:
            print(f"🔴 Rejected by Guardrails: {layer1_output.rejection_reason}")
            print("-" * 65)
            continue
            
        # Assuming we just take the first extracted claim for this test
        atomic_claim = layer1_output.claims[0]
        print(f"✅ Extracted Atomic Claim: {atomic_claim.claim_text}")
        
        # --- LAYER 2: Fact Check Lookup ---
        print("\n--- Running Layer 2.1 (Fact Check Lookup) ---")
        fc_result = lookup_fact_check(atomic_claim.claim_text)
        if fc_result.has_existing_fact_check:
            print(f"🔍 Found Existing Verdict: {fc_result.verdict} (by {fc_result.reviewer})")
            print(f"🔗 URL: {fc_result.url}")
        else:
            print("🔍 No existing fact-check found.")
            
        # --- LAYER 2: Asymmetric Retrieval ---
        print("\n--- Running Layer 2.2 (Asymmetric Retrieval) ---")
        retrieval_contexts = route_and_retrieve(atomic_claim)
        
        support_ctx = retrieval_contexts["support"]
        oppose_ctx = retrieval_contexts["oppose"]
        
        print("\n🟢 SUPPORT CONTEXT:")
        print(f"Query used: {support_ctx.queries_used[0]}")
        print(f"Retrieved {len(support_ctx.documents)} documents.")
        if support_ctx.documents:
            print(f"Top result title: {support_ctx.documents[0]['title']}")
            
        print("\n🔴 OPPOSE CONTEXT:")
        print(f"Query used: {oppose_ctx.queries_used[0]}")
        print(f"Retrieved {len(oppose_ctx.documents)} documents.")
        if oppose_ctx.documents:
            print(f"Top result title: {oppose_ctx.documents[0]['title']}")
            
        print("-" * 65)

if __name__ == "__main__":
    run_tests()
