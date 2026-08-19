# 📅 Development Timeline & Milestones

This document chronicles the step-by-step evolution of the Fact-Check Agent.

## Phase 1: Core Engine & Graph Architecture
- **Objective**: Build a LangGraph state machine with Support, Oppose, and Judge agents.
- **Actions**: 
  - Defined the `DebateState` using TypedDict.
  - Initialized Tavily for web search.
  - Built the `debate_graph` routing in FastAPI.
- **Hurdles**: Getting the agents to pass state linearly. Implemented a `turn_count` to ensure exactly one round of cross-examination before judging.

## Phase 2: Multimodal & Vision Capabilities
- **Objective**: Allow users to upload screenshots of tweets, news articles, or memes.
- **Actions**:
  - Implemented `/api/factcheck/multimodal` endpoint using `UploadFile` in FastAPI.
  - Integrated Groq's Vision models (`llama-3.2-90b-vision-preview`) to parse base64 image data and extract textual claims.

## Phase 3: The UI / UX Overhaul
- **Objective**: Create a professional, engaging user interface.
- **Actions**:
  - Bootstrapped a Next.js 14 frontend (`frontend_v2`).
  - Implemented Server-Sent Events (SSE) parsing to read `data:` chunks streamed from FastAPI.
  - Built an animated visual progress bar to keep users engaged during the 40-60 second debate process.
  - Dynamically updated UI status messages based on which LangGraph node was currently active (e.g., "Cross-examination in progress...").

## Phase 4: Model Migration & JSON Schema Fixes
- **Objective**: Fix strict tool-calling validation errors from API providers.
- **Actions**:
  - Shifted extraction and Judge models to `openai/gpt-oss-120b` via the Groq proxy.
  - Used the `Instructor` library with `Mode.JSON` to force raw JSON output, completely bypassing native Tool Calling schemas that were causing `400 Bad Request` errors.

## Phase 5: LLM Alignment Engineering
- **Objective**: Prevent the AI from refusing to "support" dangerous or false claims during the debate phase.
- **Actions**:
  - Completely overhauled the System Prompts.
  - Re-contextualized the prompt as a "simulated environment" where the agent is a "rigorous fact-checker playing Devil's Advocate."
  - Instructed the model to never break character or issue moral refusals.

## Phase 6: Cloud Deployment (Vercel + Render)
- **Objective**: Take the application live on the public internet.
- **Actions**:
  - Dockerized the backend specifically to handle Playwright Chromium binary installations.
  - Pushed to GitHub and integrated with Render (Backend) and Vercel (Frontend).
- **Deployment Hurdles Overcome**:
  - Fixed a missing `playwright` package in `requirements.txt`.
  - Solved a Render Port Binding Timeout by dynamically exposing `$PORT` in the Dockerfile `CMD`.
  - Fixed an Out-Of-Memory (OOM 512MB) crash on the Render Free Tier by ruthlessly stripping PyTorch and `sentence-transformers` from the dependency tree.
  - Fixed a missing `python-multipart` library preventing FastAPI from parsing image uploads.
