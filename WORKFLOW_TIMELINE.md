# Development Workflow & Timeline

This document tracks the chronological evolution of the Fact Check Debate Engine, highlighting how features were added, replaced, and optimized to arrive at the current production-ready V2 architecture.

## Phase 1: Initial Foundation (V1)
- **Goal**: Build a simple fact-checking bot.
- **Tech Stack**: Python, FastAPI, SQLite, simple HTML/JS frontend.
- **Architecture**: A straightforward pipeline where a user submits a claim, the backend searches the web using Tavily and Playwright, and a single language model generates a "True/False" verdict.
- **LLM Engine**: Groq (LLaMA 3) for fast text generation.
- **Outcome**: A functional but basic MVP. It lacked depth in analyzing complex, multi-faceted claims and didn't provide a compelling user experience.

## Phase 2: The Multi-Agent Debate Upgrade (V2)
- **Goal**: Improve reasoning quality and user engagement by introducing autonomous agents.
- **Architecture Change**: Integrated **LangGraph** to build a state machine.
- **New Workflow**:
  - **Layer 1 (Extraction)**: Added an Instructor-powered agent to evaluate guardrails and break complex claims into "atomic claims."
  - **Layer 2 (Dual Retrieval)**: Split the retrieval into two streams—one actively searching for evidence to *support* the claim, and one searching for evidence to *oppose* it.
  - **Layer 3 (Debate)**: Created a `Support Agent` and `Oppose Agent`. These agents use the retrieved context to build cases, then cross-examine each other.
  - **Layer 4 (Judge)**: Added an impartial `Judge Agent` to review the debate transcript and issue a final structured verdict (using Pydantic schema).

## Phase 3: Frontend Overhaul & Next.js Migration
- **Goal**: Replace the basic HTML file with a modern, dynamic UI.
- **Migration**: Bootstrapped a **Next.js** application (`frontend_v2`) using React and Tailwind CSS.
- **Design System**: Implemented a "Neumorphic" design aesthetic with soft shadows, dynamic layouts, and a clean results dashboard.
- **Real-Time Streaming**: Implemented Server-Sent Events (SSE) via `sse-starlette` in the FastAPI backend. The LangGraph `astream_events` API was hooked up to stream the debate tokens in real-time to the Next.js frontend, creating a "live debate" experience.

## Phase 4: The Gemini Migration & Rate Limit Challenges
- **Event**: Attempted to migrate the entire LLM backbone from Groq to Google Gemini (`gemini-1.5-flash` and `gemini-1.5-pro` for Vision) via `langchain-google-genai`.
- **Challenge 1 (Streaming Types)**: Gemini's LangChain integration streamed chunks as deeply nested lists instead of flat strings, causing the frontend to break.
  - *Fix*: Wrote a custom token parser in `api.py` to recursively extract text from Gemini's nested chunk objects.
- **Challenge 2 (429 Rate Limits)**: Gemini's free tier has a strict 20 Requests-Per-Minute limit. The concurrent nature of the debate agents caused immediate 429 `RESOURCE_EXHAUSTED` crashes.
  - *Fix*: Implemented a robust exponential backoff and retry loop in `layer_extractor.py` and `agents.py`. Added a regex parser to extract the specific Google `Retry-After` header to dynamically sleep the backend.

## Phase 5: Concurrency Bugs & Reverting to Groq
- **Event**: Attempted to speed up the debate by running the `Support Agent` and `Oppose Agent` in parallel using Python's `asyncio.gather`.
- **Challenge 1 (InvalidUpdateError)**: LangGraph threw an `INVALID_CONCURRENT_GRAPH_UPDATE` error because both parallel nodes attempted to update the exact same state key (`current_node`) simultaneously.
  - *Fix*: Refactored the agent nodes to return partial state dictionaries (`{"support_case": ...}` and `{"oppose_case": ...}`) and entirely removed the conflicting `current_node` key from their returns.
- **Strategic Revert**: Due to ongoing issues with Gemini's restrictive 20 RPM free-tier, a strategic decision was made to revert the entire pipeline back to **Groq (openai/gpt-oss-120b)** and **Groq Vision (LLaMA 3.2 90B Vision)**.
  - *Outcome*: Groq provides vastly higher throughput (Tokens-Per-Minute) and native string streaming, resulting in a lightning-fast, highly stable debate engine.

## Final Architecture & Workflow
The project now stands as a highly optimized, robust system:
1. **User Input**: User submits text (or an image) to the Next.js frontend.
2. **Vision/Guardrails**: Groq Vision extracts text; Groq Instructor verifies domain constraints.
3. **Retrieval**: Tavily + Playwright fetch opposing contexts.
4. **Parallel Debate**: LangGraph executes `Support Agent` and `Oppose Agent` simultaneously. They yield SSE tokens directly to the UI.
5. **Verdict**: The `Judge Agent` evaluates the debate and returns a structured JSON verdict (Confidence, Verdict, Summary).
6. **UI Polish**: The Next.js frontend dynamically renders the debate, clears status messages elegantly, and formats confidence scores strictly out of 100%.
