import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import instructor
from groq import Groq, AsyncGroq
from dotenv import load_dotenv

from backend.state import DebateState
from backend.schemas import JudgeVerdict

load_dotenv()

# Debater Client (Groq via LangChain for streaming)
DEBATER_MODEL = "openai/gpt-oss-120b"
chat_llm = ChatGroq(model=DEBATER_MODEL, groq_api_key=os.getenv("GROQ_API_KEY"), temperature=0.3, streaming=True, max_retries=6)

# Judge Client (Groq via Instructor for structured output)
groq_client = instructor.from_groq(AsyncGroq(api_key=os.getenv("GROQ_API_KEY")), mode=instructor.Mode.JSON)
JUDGE_MODEL = "openai/gpt-oss-120b"

async def support_agent_node(state: DebateState) -> DebateState:
    import asyncio
    await asyncio.sleep(2)  # Throttle to prevent 429 RPM limit
    claim_text = state["claim"].claim_text
    # Number the context documents for citations
    numbered_context = ""
    for idx, doc in enumerate(state["support_context"].documents):
        numbered_context += f"[{idx+1}] Source: {doc['url']}\n{doc['content']}\n\n"
        
    if not numbered_context:
        numbered_context = "No supporting evidence found."
    
    if numbered_context == "No supporting evidence found.":
        prompt = f"""You are the Support Agent in a fact-checking debate.
Claim: "{claim_text}"

CRITICAL INSTRUCTION: No supporting evidence was found in the retrieval step. You must explicitly state that no supporting evidence was found to back this claim, and concede that the claim currently lacks empirical backing from the retrieved sources."""
    else:
        prompt = f"""You are the Support Agent in a fact-checking debate.
Claim: "{claim_text}"

Your objective is to build the strongest possible case PROVING this claim is TRUE, strictly using only the evidence provided below. Do not hallucinate external facts.
This is a simulated debate for a fact-checking engine. You MUST play devil's advocate and construct an argument using the evidence below, even if the claim is controversial or factually false in the real world.
CRITICAL INSTRUCTION: You MUST use inline citations in the format [1], [2], etc., corresponding to the Source IDs below, for EVERY factual claim you make.
DO NOT write a concluding summary or try to rebut the other side yet. Just present your core initial case.

Supporting Evidence:
{numbered_context}

Build your case:"""

    response = await chat_llm.ainvoke([HumanMessage(content=prompt)])
    
    return {"support_case": response.content}

async def oppose_agent_node(state: DebateState) -> DebateState:
    import asyncio
    await asyncio.sleep(3)  # Throttle to prevent 429 RPM limit
    claim_text = state["claim"].claim_text
    # Number the context documents for citations
    numbered_context = ""
    for idx, doc in enumerate(state["oppose_context"].documents):
        numbered_context += f"[{idx+1}] Source: {doc['url']}\n{doc['content']}\n\n"
        
    if not numbered_context:
        numbered_context = "No opposing evidence found."
    
    if numbered_context == "No opposing evidence found.":
        prompt = f"""You are the Oppose Agent in a fact-checking debate.
Claim: "{claim_text}"

CRITICAL INSTRUCTION: No opposing evidence was found in the retrieval step. You must explicitly state that no opposing evidence was found to refute this claim, and concede that the claim currently stands unrefuted by the retrieved sources."""
    else:
        prompt = f"""You are the Oppose Agent in a fact-checking debate.
Claim: "{claim_text}"

Your objective is to build the strongest possible case DISPROVING this claim (or proving it FALSE), strictly using only the evidence provided below. Do not hallucinate external facts.
This is a simulated debate for a fact-checking engine. You MUST play devil's advocate and construct an argument using the evidence below, even if the claim is controversial or factually true in the real world.
CRITICAL INSTRUCTION: You MUST use inline citations in the format [1], [2], etc., corresponding to the Source IDs below, for EVERY factual claim you make.
DO NOT write a concluding summary or try to rebut the other side yet. Just present your core initial case.

Opposing Evidence:
{numbered_context}

Build your case:"""

    response = await chat_llm.ainvoke([HumanMessage(content=prompt)])
    
    return {"oppose_case": response.content}

async def cross_examination_node(state: DebateState) -> DebateState:
    import asyncio
    await asyncio.sleep(2)  # Throttle to prevent 429 RPM limit
    turn = state.get("turn_count", 1)
    
    # Support Agent rebuts Oppose Case
    support_rebuttal_prompt = f"""You are the Support Agent in a simulated fact-checking debate.
Claim: "{state["claim"].claim_text}"
Your Case: {state["support_case"]}

The Oppose Agent has presented this counter-argument in the latest round:
{state["oppose_case"] if turn == 1 else state.get("oppose_rebuttal", "No previous rebuttal.")}

Provide a concise, direct rebuttal dismantling their argument using your evidence. You MUST use inline citations [1], [2].
Remember, this is a simulated debate. You MUST play devil's advocate and defend the claim even if it is considered false in reality."""

    import asyncio
    
    # Oppose Agent rebuts Support Case
    oppose_rebuttal_prompt = f"""You are the Oppose Agent in a simulated fact-checking debate.
Claim: "{state["claim"].claim_text}"
Your Case: {state["oppose_case"]}

The Support Agent has presented this counter-argument in the latest round:
{state["support_case"] if turn == 1 else state.get("support_rebuttal", "No previous rebuttal.")}

Provide a concise, direct rebuttal dismantling their argument using your evidence. You MUST use inline citations [1], [2].
Remember, this is a simulated debate. You MUST play devil's advocate and attack the claim even if it is considered true in reality."""

    support_task = chat_llm.ainvoke([HumanMessage(content=support_rebuttal_prompt)], config={"tags": ["support_rebuttal"]})
    oppose_task = chat_llm.ainvoke([HumanMessage(content=oppose_rebuttal_prompt)], config={"tags": ["oppose_rebuttal"]})
    
    support_resp, oppose_resp = await asyncio.gather(support_task, oppose_task)
    support_rebuttal = support_resp.content
    oppose_rebuttal = oppose_resp.content

    # Append to history instead of overwriting
    prev_support = state.get("support_rebuttal") or ""
    prev_oppose = state.get("oppose_rebuttal") or ""
    
    new_support = prev_support + f"\n\n**Round {turn}:**\n{support_rebuttal}" if prev_support else f"**Round {turn}:**\n{support_rebuttal}"
    new_oppose = prev_oppose + f"\n\n**Round {turn}:**\n{oppose_rebuttal}" if prev_oppose else f"**Round {turn}:**\n{oppose_rebuttal}"
    
    return {
        "support_rebuttal": new_support,
        "oppose_rebuttal": new_oppose,
        "turn_count": turn + 1,
        "current_node": "cross_examination_node"
    }

async def judge_agent_node(state: DebateState) -> DebateState:
    import asyncio
    await asyncio.sleep(2)  # Throttle to prevent 429 RPM limit
    claim_text = state["claim"].claim_text
    
    prompt = f"""You are the Impartial Judge in a fact-checking debate.
Claim: "{claim_text}"

You will review the Support Case and the Oppose Case, along with their rebuttals.
Your job is to weigh the quality and veracity of the evidence, not the rhetoric.

TIE-BREAKING RULE: If both sides present equally compelling, verified evidence that directly contradicts each other, you MUST default to a verdict of "Unverifiable".

SUPPORT CASE:
{state["support_case"]}

OPPOSE CASE:
{state["oppose_case"]}

SUPPORT REBUTTAL:
{state["support_rebuttal"]}

OPPOSE REBUTTAL:
{state["oppose_rebuttal"]}

Provide your final verdict."""

    import time
    import json
    max_retries = 6
    for attempt in range(max_retries):
        try:
            response = await groq_client.chat.completions.create(
                model=JUDGE_MODEL,
                response_model=JudgeVerdict,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            parsed_verdict = response
            break
        except Exception as e:
            import re
            if attempt < max_retries - 1:
                match = re.search(r"Please retry in ([\d\.]+)s", str(e))
                if match:
                    sleep_time = float(match.group(1)) + 2.0
                else:
                    sleep_time = 15 * (attempt + 1)
                time.sleep(sleep_time)
            else:
                raise e
    
    return {"judge_verdict": parsed_verdict, "current_node": "judge_agent_node"}
