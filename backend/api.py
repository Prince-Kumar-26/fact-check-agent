from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import re

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.layer_extractor import process_layer1, extract_from_image
from backend.retrieval_router import route_and_retrieve
from backend.graph import debate_graph
from backend.schemas import Citation
from backend.database import engine, get_db, Base
from backend.models import FactCheckRecord

# Tables are managed by Alembic migrations
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fact Check Debate API V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def sanitize_claim(claim: str) -> str:
    """Removes HTML tags and checks for basic prompt injection."""
    clean = re.sub(r'<[^>]*>', '', claim)
    lower_clean = clean.lower()
    suspicious = ["ignore all previous instructions", "system prompt", "you are now", "forget previous"]
    for phrase in suspicious:
        if phrase in lower_clean:
            raise HTTPException(status_code=400, detail="Malicious prompt injection detected.")
    return clean.strip()

class FactCheckRequest(BaseModel):
    claim: str

class FactCheckResponse(BaseModel):
    original_claim: str
    extracted_claim: str
    status: str
    rejection_reason: Optional[str] = None
    support_case: Optional[str] = None
    oppose_case: Optional[str] = None
    support_rebuttal: Optional[str] = None
    oppose_rebuttal: Optional[str] = None
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None
    citations: Optional[List[Citation]] = None

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(FactCheckRecord).order_by(FactCheckRecord.created_at.desc()).limit(20).all()
    return records

@app.post("/api/factcheck", response_model=FactCheckResponse)
@limiter.limit("10/minute")
def run_factcheck(request: Request, body: FactCheckRequest, db: Session = Depends(get_db)):
    sanitized_claim = sanitize_claim(body.claim)
    # Check cache
    existing = db.query(FactCheckRecord).filter(FactCheckRecord.original_claim == sanitized_claim).first()
    if existing and existing.status == "COMPLETED":
        return FactCheckResponse(
            original_claim=existing.original_claim,
            extracted_claim=existing.extracted_claim,
            status=existing.status,
            rejection_reason=existing.rejection_reason,
            support_case=existing.support_case,
            oppose_case=existing.oppose_case,
            support_rebuttal=existing.support_rebuttal,
            oppose_rebuttal=existing.oppose_rebuttal,
            verdict=existing.verdict,
            confidence=existing.confidence,
            summary=existing.summary,
            citations=[Citation(**c) for c in json.loads(existing.citations_json)] if existing.citations_json else None
        )

    layer1_out = process_layer1(sanitized_claim)
    if not layer1_out.is_valid:
        record = FactCheckRecord(
            original_claim=sanitized_claim,
            extracted_claim="",
            status="REJECTED",
            rejection_reason=layer1_out.rejection_reason
        )
        db.add(record)
        db.commit()
        return FactCheckResponse(
            original_claim=sanitized_claim,
            extracted_claim="",
            status="REJECTED",
            rejection_reason=layer1_out.rejection_reason
        )
        
    if not layer1_out.claims:
        return FactCheckResponse(
            original_claim=sanitized_claim,
            extracted_claim="",
            status="REJECTED",
            rejection_reason="Failed to extract verifiable claims from the input (likely due to LLM rate limits or parsing errors)."
        )
        
    atomic_claim = layer1_out.claims[0]
    contexts = route_and_retrieve(atomic_claim)
    
    initial_state = {
        "claim": atomic_claim,
        "support_context": contexts["support"],
        "oppose_context": contexts["oppose"],
        "support_case": None,
        "oppose_case": None,
        "support_rebuttal": None,
        "oppose_rebuttal": None,
        "judge_verdict": None,
        "current_node": "start",
        "turn_count": 1
    }
    
    try:
        from langfuse.callback import CallbackHandler
        langfuse_handler = CallbackHandler()
        callbacks = [langfuse_handler]
    except ImportError:
        callbacks = []

    final_state = debate_graph.invoke(initial_state, config={"callbacks": callbacks})
    verdict_obj = final_state.get("judge_verdict")
    
    record = FactCheckRecord(
        original_claim=sanitized_claim,
        extracted_claim=atomic_claim.claim_text,
        status="COMPLETED",
        support_case=final_state.get("support_case"),
        oppose_case=final_state.get("oppose_case"),
        support_rebuttal=final_state.get("support_rebuttal"),
        oppose_rebuttal=final_state.get("oppose_rebuttal"),
        verdict=verdict_obj.verdict if verdict_obj else None,
        confidence=verdict_obj.confidence if verdict_obj else None,
        summary=verdict_obj.summary if verdict_obj else None,
        citations_json=json.dumps([c.model_dump() for c in verdict_obj.citations]) if verdict_obj and verdict_obj.citations else None
    )
    db.add(record)
    db.commit()
    
    return FactCheckResponse(
        original_claim=sanitized_claim,
        extracted_claim=atomic_claim.claim_text,
        status="COMPLETED",
        support_case=final_state.get("support_case"),
        oppose_case=final_state.get("oppose_case"),
        support_rebuttal=final_state.get("support_rebuttal"),
        oppose_rebuttal=final_state.get("oppose_rebuttal"),
        verdict=verdict_obj.verdict if verdict_obj else None,
        confidence=verdict_obj.confidence if verdict_obj else None,
        summary=verdict_obj.summary if verdict_obj else None,
        citations=verdict_obj.citations if verdict_obj else None
    )

@app.post("/api/factcheck/multimodal", response_model=FactCheckResponse)
async def run_factcheck_multimodal(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    # Extract claims from image using vision model
    claims = extract_from_image(file_bytes)
    
    if not claims:
        return FactCheckResponse(
            original_claim="Image Upload",
            extracted_claim="",
            status="REJECTED",
            rejection_reason="No verifiable claims found in the image."
        )
        
    atomic_claim = claims[0]
    # We pass the internal request directly to run_factcheck
    class MockRequest:
        pass
    mock_req = MockRequest()
    setattr(mock_req, 'client', type('obj', (object,), {'host': '127.0.0.1'}))
    
    fact_req = FactCheckRequest(claim=atomic_claim.claim_text)
    return run_factcheck(request=mock_req, body=fact_req, db=db)
    
@app.post("/api/factcheck/stream")
@limiter.limit("5/minute")
async def run_factcheck_stream(request: Request, body: FactCheckRequest):
    """Real-Time SSE Streaming Endpoint"""
    sanitized_claim = sanitize_claim(body.claim)
    async def event_generator():
        try:
            layer1_out = await asyncio.to_thread(process_layer1, sanitized_claim)
            if not layer1_out.is_valid:
                yield {"event": "error", "data": json.dumps({"reason": layer1_out.rejection_reason})}
                return
                
            if not layer1_out.claims:
                yield {"event": "error", "data": json.dumps({"reason": "Failed to extract verifiable claims from the input (likely due to LLM rate limits). Please try again later."})}
                return
                
            atomic_claim = layer1_out.claims[0]
            yield {"event": "status", "data": json.dumps({"message": f"Extracted Claim: {atomic_claim.claim_text}"})}
            
            yield {"event": "status", "data": json.dumps({"message": "Retrieving evidence from Web and Knowledge Base..."})}
            contexts = await asyncio.to_thread(route_and_retrieve, atomic_claim)
            
            initial_state = {
                "claim": atomic_claim,
                "support_context": contexts["support"],
                "oppose_context": contexts["oppose"],
                "support_case": None,
                "oppose_case": None,
                "support_rebuttal": None,
                "oppose_rebuttal": None,
                "judge_verdict": None,
                "current_node": "start",
                "turn_count": 1
            }
            
            yield {"event": "status", "data": json.dumps({"message": "Starting Agent Debate..."})}
            
            try:
                from langfuse.callback import CallbackHandler
                langfuse_handler = CallbackHandler()
                callbacks = [langfuse_handler]
            except ImportError:
                callbacks = []

            # Stream LangGraph events
            async for event in debate_graph.astream_events(initial_state, config={"callbacks": callbacks}, version="v1"):
                kind = event["event"]
                
                if kind == "on_chain_start" and event["name"] == "judge_agent_node":
                    yield {"event": "status", "data": json.dumps({"message": "Judge Agent is reviewing evidence..."})}
                    
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        token_text = ""
                        if isinstance(chunk.content, str):
                            token_text = chunk.content
                        elif isinstance(chunk.content, list):
                            for part in chunk.content:
                                if isinstance(part, dict) and "text" in part:
                                    token_text += part["text"]
                        
                        if token_text:
                            node_name = event.get("metadata", {}).get("langgraph_node")
                            tags = event.get("metadata", {}).get("tags", [])
                            if "support_rebuttal" in tags:
                                node_name = "support_rebuttal"
                            elif "oppose_rebuttal" in tags:
                                node_name = "oppose_rebuttal"
                            yield {"event": "token", "data": json.dumps({"token": token_text, "node": node_name})}
                elif kind == "on_chain_end":
                    if event["name"] == "LangGraph":
                        final_state = event["data"].get("output", {})
                        verdict_obj = None
                        if "judge_verdict" in final_state:
                            verdict_obj = final_state["judge_verdict"]
                        else:
                            # In astream_events, output might be wrapped in the node name e.g. {"judge_agent": {...}}
                            for key, value in final_state.items():
                                if isinstance(value, dict) and "judge_verdict" in value:
                                    verdict_obj = value["judge_verdict"]
                                    break
                                    
                        if verdict_obj:
                            yield {"event": "verdict", "data": json.dumps({
                                "verdict": verdict_obj.verdict,
                                "confidence": verdict_obj.confidence,
                                "summary": verdict_obj.summary
                            })}
            
            yield {"event": "done", "data": json.dumps({"message": "Debate completed."})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"reason": f"API Error: {str(e)} - Please try again in a few moments."})}
            return
        
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
