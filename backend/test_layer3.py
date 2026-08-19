import json
from backend.layer_extractor import process_layer1
from backend.retrieval_router import route_and_retrieve
from backend.graph import debate_graph

def run_test():
    print("\n================= RUNNING LAYER 3 TEST SUITE =================\n")
    
    test_claim = "mRNA COVID-19 vaccines can permanently alter your DNA."
    print(f"Original Input: {test_claim}\n")
    
    # LAYER 1
    layer1_out = process_layer1(test_claim)
    if not layer1_out.is_valid:
        print("Layer 1 Rejected:", layer1_out.rejection_reason)
        return
        
    atomic_claim = layer1_out.claims[0]
    print(f"✅ Layer 1 Extracted: {atomic_claim.claim_text}")
    
    # LAYER 2
    contexts = route_and_retrieve(atomic_claim)
    print(f"✅ Layer 2 Retrieved Support Docs: {len(contexts['support'].documents)}")
    print(f"✅ Layer 2 Retrieved Oppose Docs: {len(contexts['oppose'].documents)}")
    
    # LAYER 3 - The Debate Engine
    print("\n--- Starting LangGraph Debate Engine ---")
    
    initial_state = {
        "claim": atomic_claim,
        "support_context": contexts["support"],
        "oppose_context": contexts["oppose"],
        "support_case": None,
        "oppose_case": None,
        "support_rebuttal": None,
        "oppose_rebuttal": None,
        "judge_verdict": None,
        "current_node": "start"
    }
    
    final_state = debate_graph.invoke(initial_state)
    
    print("\n🟢 SUPPORT CASE:")
    print(final_state["support_case"])
    
    print("\n🔴 OPPOSE CASE:")
    print(final_state["oppose_case"])
    
    print("\n🟢 SUPPORT REBUTTAL:")
    print(final_state["support_rebuttal"])
    
    print("\n🔴 OPPOSE REBUTTAL:")
    print(final_state["oppose_rebuttal"])
    
    print("\n================ FINAL JUDGMENT ================")
    verdict = final_state["judge_verdict"]
    print(f"VERDICT: {verdict.verdict} (Confidence: {verdict.confidence}%)")
    print(f"SUMMARY: {verdict.summary}")
    print("CITATIONS:")
    for citation in verdict.citations:
        print(f"  - {citation.title} ({citation.url})")
        
if __name__ == "__main__":
    run_test()
