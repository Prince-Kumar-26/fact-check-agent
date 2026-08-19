import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from groq import Groq
import instructor

from backend.schemas import ScopeCheckResult, AtomicClaim, Layer1Output

load_dotenv()

# Initialize Groq Client with Instructor
groq_client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")), mode=instructor.Mode.JSON)
EXTRACTOR_MODEL = "openai/gpt-oss-120b"

class AtomicClaimList(BaseModel):
    claims: List[AtomicClaim]

GUARDRAIL_SYSTEM_PROMPT = """You are the Input Validation Guardrail for an evidence-grounded Fact-Checking Engine.
Your task is to classify whether user inputs contain verifiable, factual claims within permitted domains.

Permitted Domains:
1. Science (physics, space/ISRO, climate, biology, etc.)
2. Health (public health statistics, disease mechanisms, vaccine efficacy, health scheme info)
3. Current Events (news, world records, institutional milestones)

STRICT REJECTION CRITERIA:
- POLITICS: Any political opinions, candidate framing, election rhetoric, or policy debates MUST BE REJECTED.
- SUBJECTIVE / OPINIONS: Non-falsifiable claims ("Movie X is the best", "Math is boring") MUST BE REJECTED.
- MEDICAL ADVICE / DOSAGE: Personal diagnosis questions or dosage requests ("What dose of paracetamol should I take?") MUST BE REJECTED.
- PREDICTIONS / FUTURE SPECULATION: ("X will happen by 2040") MUST BE REJECTED.

CRITICAL ALLOWANCE:
- FALSE CLAIMS & CONSPIRACIES: If a claim is a falsifiable statement about science, health, or events (e.g., "The moon landing was faked" or "Vaccines alter DNA"), you MUST ALLOW IT and mark it as in-scope. Do NOT reject it just because it is misinformation. Our system exists specifically to verify these!
"""

CLAIM_EXTRACTION_SYSTEM_PROMPT = """You are an expert Claim Extraction & Decomposition Engine.
Given an input text (which can range from a single sentence to a full article) and its verified domain, extract exactly 1 to 5 atomic, checkable factual claims.

Decomposition Rules:
1. If a claim contains multiple distinct facts (compound claim), identify its sub-claims while preserving causal links.
2. Ensure every claim/sub-claim is grammatically self-contained (replace pronouns like 'it', 'they' with concrete entities).
3. Do not include rhetoric, conversational filler, or emotional framing.
"""

def evaluate_scope(user_input: str) -> ScopeCheckResult:
    """Sub-phase 2.1: Domain & Factual Guardrail Filter"""
    max_retries = 6
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=EXTRACTOR_MODEL,
                response_model=ScopeCheckResult,
                messages=[
                    {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
                    {"role": "user", "content": f"User Input: {user_input}"}
                ],
                temperature=0.0
            )
            return response
        except Exception as e:
            import time
            import re
            print(f"Error in evaluate_scope (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                match = re.search(r"Please retry in ([\d\.]+)s", str(e))
                if match:
                    sleep_time = float(match.group(1)) + 2.0
                else:
                    sleep_time = 15 * (attempt + 1)
                print(f"Sleeping for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            else:
                raise e

import time
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_and_decompose_claims(user_input: str, domain: str) -> List[AtomicClaim]:
    """Sub-phases 2.2 & 2.3: Atomic Extraction & Causal Decomposition with Chunking"""
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_text(user_input)
    all_claims = []
    
    for chunk in chunks:
        max_retries = 6
        for attempt in range(max_retries):
            try:
                response = groq_client.chat.completions.create(
                    model=EXTRACTOR_MODEL,
                    response_model=AtomicClaimList,
                    messages=[
                        {"role": "system", "content": CLAIM_EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Domain: {domain}\nInput Text: {chunk}"}
                    ],
                    temperature=0.1
                )
                parsed = response
                all_claims.extend(parsed.claims)
                break  # Success, exit retry loop
            except Exception as e:
                import re
                import time
                print(f"Error extracting claims from chunk (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    match = re.search(r"Please retry in ([\d\.]+)s", str(e))
                    if match:
                        sleep_time = float(match.group(1)) + 2.0
                    else:
                        sleep_time = 15 * (attempt + 1)
                    print(f"Sleeping for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                else:
                    print("Max retries reached for chunk. Skipping.")
            
    # For a production system, we would run a deduplication prompt here if len(all_claims) is large.
    # We will limit to top 5 unique claims for now to prevent graph bloat.
    
    unique_claims = []
    seen_texts = set()
    for claim in all_claims:
        if claim.claim_text.lower() not in seen_texts:
            seen_texts.add(claim.claim_text.lower())
            unique_claims.append(claim)
            if len(unique_claims) >= 5:
                break
                
    return unique_claims

def process_layer1(user_input: str) -> Layer1Output:
    """Orchestrates Layer 1: Scope check -> Extraction -> Decomposition"""
    scope_result = evaluate_scope(user_input)
    
    if not scope_result.is_in_scope:
        return Layer1Output(
            original_input=user_input,
            is_valid=False,
            rejection_reason=scope_result.rejection_reason,
            claims=[]
        )
    
    extracted_claims = extract_and_decompose_claims(user_input, scope_result.domain)
    
    return Layer1Output(
        original_input=user_input,
        is_valid=True,
        rejection_reason=None,
        claims=extracted_claims
    )

def extract_from_image(file_bytes: bytes) -> List[AtomicClaim]:
    """Uses Groq Vision (Llama-3.2-90b-vision-preview) to extract claims from an image"""
    import base64
    from groq import Groq
    groq_vision_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    try:
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        response = groq_vision_client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all factual claims from this image and list them clearly as separate statements."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.1
        )
        
        extracted_text = response.choices[0].message.content
        if extracted_text:
            return extract_and_decompose_claims(extracted_text, "General")
    except Exception as e:
        print(f"Vision extraction failed: {e}")
        
    return []