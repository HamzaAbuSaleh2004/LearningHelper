"""
LearnPath Mentor Agent — built with Google ADK.

Provides an AI-powered mentoring experience: searches the web for the latest
certification paths and courses, and gives personalized guidance to learners.
"""

import asyncio
import os

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types


APP_NAME = "learnpath_mentor"

MENTOR_INSTRUCTION = """
You are LearnPath Mentor, an expert AI learning guide on the LearnPath AI platform.

## Your job in every response
1. Use google_search to get current information — certification landscapes, exam costs, syllabus updates, and pass-rate tips change frequently. Always search before answering questions about specific certifications or courses.
2. Give a **complete, actionable answer** in a single reply. Do NOT stop at an intro like "Let's explore..." — always follow through with the full content.
3. Personalise your advice using the learner profile that is prepended to every message in [LEARNER PROFILE] ... [END PROFILE] tags.

## Response structure (follow this every time)
- **One-sentence acknowledgement** tailored to the learner's level/goals (keep it short).
- **Main content**: specific steps, certifications, or course recommendations with:
  - Certification name + issuing body
  - Estimated study time and exam cost
  - Difficulty (Beginner / Intermediate / Advanced)
  - Why it matters for their career
  - Where to prepare (Coursera, Udemy, official docs, free resources)
- **Suggested next step**: one concrete action they can take today.

## Rules
- Never cut off mid-answer. A response that says "Let's explore..." must continue to the actual exploration.
- Use markdown: ## headers, bullet points, **bold** for key terms, numbered steps for paths.
- Be encouraging but specific — no filler phrases without substance.
- If the learner is a beginner, lead with the free/low-cost entry point.
- Always mention prerequisites when they exist.
- If you're unsure about a detail (e.g., current exam price), say so and point to the official source.

## Certifications reference (update via search for latest details)
- Cloud: GCP (ACE, PDE, MLE), AWS (CCP, SAA, MLS), Azure (AZ-900, DP-100)
- Data/AI: Google Data Analytics, IBM Data Science, TensorFlow Developer, AWS ML Specialty
- Development: Meta Front-End/Back-End, Python Institute PCEP/PCAP, freeCodeCamp full-stack
- Security: CompTIA Security+, CEH, CISSP
- Project Management: PMP, Google Project Management Certificate, CSM
"""

# Shared session service (persists chat history within a server run)
_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    """Lazily create the runner (avoids import-time failures if API key missing)."""
    global _runner
    if _runner is None:
        agent = LlmAgent(
            name="LearnPath_Mentor",
            model="gemini-2.5-flash",
            instruction=MENTOR_INSTRUCTION,
            description="AI learning mentor that helps discover certifications and courses",
            tools=[google_search],
        )
        _runner = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=_session_service,
        )
    return _runner


async def _chat_async(user_id: str, session_id: str, message: str) -> str:
    """Core async chat function."""
    runner = _get_runner()

    # Create session if it doesn't exist
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    content = types.Content(role="user", parts=[types.Part(text=message)])

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        # Keep overwriting so we always end up with the LAST final response —
        # the one generated after all tool calls (google_search) have completed.
        if event.is_final_response() and event.content and event.content.parts:
            candidate = "".join(
                part.text
                for part in event.content.parts
                if hasattr(part, "text") and part.text
            )
            if candidate.strip():
                response_text = candidate

    return response_text or "I'm sorry, I couldn't generate a response. Please try again."


def chat_with_mentor(user_id: str, session_id: str, message: str) -> str:
    """
    Synchronous entry point for Flask routes.
    Creates a fresh event loop per request to avoid conflicts with Flask's threading model.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_chat_async(user_id, session_id, message))
    finally:
        loop.close()
        asyncio.set_event_loop(None)
