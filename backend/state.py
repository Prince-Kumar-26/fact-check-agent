from typing import TypedDict, List, Optional
from backend.schemas import AtomicClaim, RetrievalContext, JudgeVerdict

class DebateState(TypedDict):
    # Initial input
    claim: AtomicClaim
    
    # Layer 2 Outputs
    support_context: Optional[RetrievalContext]
    oppose_context: Optional[RetrievalContext]
    
    # Layer 3 (Debate Engine) Outputs
    support_case: Optional[str]
    oppose_case: Optional[str]
    support_rebuttal: Optional[str]
    oppose_rebuttal: Optional[str]
    
    # Final Judge Verdict
    judge_verdict: Optional[JudgeVerdict]
    
    # LangGraph routing/control flags
    current_node: str
    turn_count: int
