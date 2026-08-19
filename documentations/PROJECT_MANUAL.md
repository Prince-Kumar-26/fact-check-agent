# 📖 The Fact-Check Agent Manual

> *A comprehensive "Start-to-Finish" guide to the Fact-Check Agent V2.*

## 1. Introduction
This project was born out of the need for an autonomous AI system capable of verifying complex claims (both textual and image-based) by actively combating LLM bias. Traditional LLMs hallucinate or rely on outdated pre-training data. This agent instead orchestrates a **simulated courtroom debate**.

## 2. Core Concept: The Debate Graph
The core innovation is the use of **LangGraph**, a state-machine framework for LLMs.
Instead of asking a single AI to verify a claim, the system splits into three personas:
1. **The Support Agent**: Tasked with finding any possible evidence on the web to *prove* the claim is true. It plays "Devil's Advocate".
2. **The Oppose Agent**: Tasked with finding any possible evidence to *debunk* the claim.
3. **The Judge Agent**: Acts as an impartial jury. It reviews the transcripts of the Support and Oppose agents (including their rebuttals) and issues a final, structured verdict.

## 3. How a Request Flows Through the System
1. **User Input**: The user submits a text claim or uploads an image.
2. **Extraction (If Image)**: If an image is uploaded, it is passed to a Vision Model via Groq, which extracts the central claims being made in the image.
3. **Graph Invocation**: The backend initiates the `debate_graph` (LangGraph).
4. **Research Phase**:
   - The Support and Oppose agents use the **Tavily Search API** to scour the web.
   - If a URL looks promising, they use **Playwright** (a headless Chromium browser) to deeply scrape the text of the article.
5. **Debate Phase**: The agents draft their cases. Then, in the "Cross-Examination" node, they read each other's cases and draft rebuttals.
6. **Judgment Phase**: The Judge analyzes the final state and outputs a JSON object conforming to strict Pydantic schemas using the **Instructor** library.
7. **Streaming to UI**: Throughout this entire process, the backend streams `Server-Sent Events (SSE)` to the Next.js frontend, animating a progress bar and updating the UI text so the user knows exactly what the AI is thinking.

## 4. Key Engineering Hurdles Overcome
During development, several massive hurdles were solved:
- **LLM Alignment Refusals**: When asked to support false medical claims (e.g., "mRNA alters DNA"), the AI would refuse. We engineered complex system prompts instructing the AI that this is a *simulated* debate where it *must* play devil's advocate for the sake of rigorous verification.
- **Strict JSON Tool Calling**: Groq's tool-calling became overly strict, causing 400 Errors when smaller models hallucinated JSON keys. We solved this by using `openai/gpt-oss-120b` in `instructor.Mode.JSON` to force raw JSON output instead of native tool calls.
- **Docker Memory Limits in the Cloud**: Deploying to Render's Free Tier (512MB RAM) caused Out-Of-Memory (OOM) silent crashes. We aggressively stripped heavy dependencies like PyTorch and `sentence-transformers`, gracefully gracefully degrading Pinecone vector search while keeping Tavily web search intact.

## 5. Deployment Architecture
- **Frontend**: Next.js 14 hosted on **Vercel**. Environment variable `NEXT_PUBLIC_BACKEND_URL` securely links it to the backend.
- **Backend**: FastAPI running via Uvicorn in a Docker container on **Render**. Docker is specifically required because Playwright needs system-level Linux dependencies (like Chromium) installed to scrape websites.
