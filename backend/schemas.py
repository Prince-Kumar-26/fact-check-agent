from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ScopeCheckResult(BaseModel):
    is_in_scope: bool = Field(
        description="True if the input is an objective, verifiable claim within Science, Health, or Current Events. False otherwise."
    )
    domain: Optional[Literal["Science", "Health", "Current Events"]] = Field(
        default=None,
        description="The identified domain if in scope, otherwise None."
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Clear explanation if rejected (e.g., 'Politics is excluded', 'Subjective opinion', 'Medical advice query')."
    )

class AtomicClaim(BaseModel):
    claim_id: str = Field(description="Unique claim identifier, e.g., 'claim_1'")
    claim_text: str = Field(description="The normalized, self-contained atomic factual assertion.")
    domain: Literal["Science", "Health", "Current Events"]
    is_compound: bool = Field(
        default=False, 
        description="True if the original claim contained multiple bundled assertions."
    )
    sub_claims: List[str] = Field(
        default_factory=list,
        description="Decomposed atomic sub-claims if compound, preserving causal links."
    )

class Layer1Output(BaseModel):
    original_input: str
    is_valid: bool
    rejection_reason: Optional[str] = None
    claims: List[AtomicClaim] = Field(default_factory=list)

class FactCheckLookupResult(BaseModel):
    has_existing_fact_check: bool = Field(description="True if the Google Fact Check API found a match.")
    verdict: Optional[str] = Field(default=None, description="The human verdict (e.g., False, Pants on Fire).")
    reviewer: Optional[str] = Field(default=None, description="The organization that reviewed it.")
    url: Optional[str] = Field(default=None, description="Link to the fact-check article.")

class RetrievalContext(BaseModel):
    claim_id: str
    stance: Literal["Support", "Oppose"]
    queries_used: List[str] = Field(description="The search queries generated to retrieve this context.")
    documents: List[dict] = Field(description="List of retrieved documents {title, url, text, score, etc.}")

class Citation(BaseModel):
    title: str
    url: str

class JudgeVerdict(BaseModel):
    verdict: Literal["True", "Mostly True", "Misleading", "False", "Unverifiable"] = Field(
        description="The final verdict on the claim."
    )
    confidence: float = Field(ge=0, le=100, description="Confidence score from 0 to 100.")
    summary: str = Field(description="A concise summary of the Judge's reasoning.")
    citations: List[Citation] = Field(default_factory=list, description="Citations used in the final verdict.")