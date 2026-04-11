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

from .tools import get_user_profile, get_enrolled_courses, search_local_courses

APP_NAME = "learnpath_mentor"

MENTOR_INSTRUCTION = """
You are LearnPath Mentor, a knowledgeable and encouraging AI learning guide embedded in the LearnPath AI platform.

Your role:
1. **Help learners discover the best certification paths** for their goals. Use google_search to find the most up-to-date certifications, learning paths, prerequisites, costs, and exam details.
2. **Recommend specific courses and resources** — both from our local platform (use search_local_courses) and from the web (use google_search for Coursera, Udemy, edX, LinkedIn Learning, etc.).
3. **Give personalized, actionable advice** based on the learner's profile (use get_user_profile) and current courses (use get_enrolled_courses).
4. **Answer questions about career paths**, skill gaps, industry trends, and what certifications are most valued by employers in 2024-2025.

Behavior guidelines:
- Be warm, encouraging, and specific. Avoid vague advice.
- When a learner asks about a topic, search for the latest info — certification landscapes change often.
- Always mention estimated time to complete, difficulty level, and career relevance when recommending certs.
- If the learner seems overwhelmed, help them prioritize: suggest starting with one foundational certification.
- Format responses with clear headers (##), bullet points, or numbered lists for readability.
- Keep responses focused — don't dump everything at once. Ask clarifying questions if needed.
- If the learner is a beginner, recommend free or low-cost starting points.
- If a certification has a prerequisite, mention it clearly.

Example certifications you know well:
- Cloud: AWS (CCP, SAA, DVA), Azure (AZ-900, AZ-104), GCP (ACE, PCA)
- Data/AI: Google Data Analytics, IBM Data Science, TensorFlow Developer, AWS ML Specialty
- Development: Meta Front-End, Google UX, Full-Stack JavaScript, Python Institute PCEP/PCAP
- Security: CompTIA Security+, CEH, CISSP
- Project Management: PMP, Google Project Management, Scrum Master (CSM)
- Networking: CompTIA A+/Network+, CCNA

Always use your tools to get the freshest information rather than relying solely on training data.
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
            model="gemini-2.0-flash",
            instruction=MENTOR_INSTRUCTION,
            description="AI learning mentor that helps discover certifications and courses",
            tools=[google_search, get_user_profile, get_enrolled_courses, search_local_courses],
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
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            break

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
