import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from tavily import TavilyClient
from backend.schemas import RetrievalContext, AtomicClaim

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

from backend.browser_tool import scrape_url_content

def _tavily_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Helper to execute Tavily search and format results"""
    try:
        response = tavily_client.search(query, max_results=max_results)
        results = response.get('results', [])
        docs = []
        for r in results:
            url = r.get("url")
            # Deep Scrape the URL using Playwright
            scraped_text = scrape_url_content(url)
            # Fallback to Tavily snippet if scrape fails
            final_content = scraped_text if len(scraped_text) > 100 else r.get("content")
            
            docs.append({
                "title": r.get("title"),
                "url": url,
                "content": final_content,
                "score": r.get("score")
            })
        return docs
    except Exception as e:
        print(f"Tavily search failed for query '{query}': {e}")
        return []

from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# Lazy load sentence transformer to avoid slow startup if not needed
_encoder = None
def get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            print("WARNING: sentence_transformers not installed. Skipping Pinecone vector embeddings.")
            return None
    return _encoder

def _pinecone_search(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Query internal Pinecone vector DB"""
    try:
        encoder = get_encoder()
        if encoder is None:
            return []
            
        query_embedding = encoder.encode(query).tolist()
        results = pinecone_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        docs = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            docs.append({
                "title": metadata.get("title", "Internal Document"),
                "url": metadata.get("url", "Internal Database"),
                "content": metadata.get("text_chunk", ""),
                "score": match.get("score")
            })
        return docs
    except Exception as e:
        print(f"Pinecone search failed: {e}")
        return []

def fetch_support_evidence(claim: AtomicClaim, use_pinecone: bool = False) -> RetrievalContext:
    query = f"evidence proving {claim.claim_text}"
    documents = _tavily_search(query, max_results=2)
    
    if use_pinecone:
        internal_docs = _pinecone_search(query, top_k=2)
        documents.extend(internal_docs)
        
    return RetrievalContext(
        claim_id=claim.claim_id,
        stance="Support",
        queries_used=[query],
        documents=documents
    )

def fetch_oppose_evidence(claim: AtomicClaim, use_pinecone: bool = False) -> RetrievalContext:
    query = f"evidence disproving {claim.claim_text} or {claim.claim_text} is false"
    documents = _tavily_search(query, max_results=2)
    
    if use_pinecone:
        internal_docs = _pinecone_search(query, top_k=2)
        documents.extend(internal_docs)
        
    return RetrievalContext(
        claim_id=claim.claim_id,
        stance="Oppose",
        queries_used=[query],
        documents=documents
    )

def route_and_retrieve(claim: AtomicClaim) -> Dict[str, RetrievalContext]:
    """
    Retrieval Router: Uses Tavily, and Pinecone if domain is Science or Health.
    """
    use_pinecone = claim.domain in ["Science", "Health"]
    
    support_ctx = fetch_support_evidence(claim, use_pinecone=use_pinecone)
    oppose_ctx = fetch_oppose_evidence(claim, use_pinecone=use_pinecone)
    
    return {
        "support": support_ctx,
        "oppose": oppose_ctx
    }
