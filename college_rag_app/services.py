import asyncio
import logging
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

from .agent.agent import root_agent
from .config import Config

logger = logging.getLogger(__name__)

# Initialize database and runner services
try:
    session_service = DatabaseSessionService(db_url=Config.DATABASE_URL)
    runner = Runner(
        agent=root_agent,
        app_name=Config.APP_NAME,
        session_service=session_service
    )
except Exception as e:
    logger.critical(f"Failed to initialize agent services: {e}")
    raise

async def run_agent_async(user_id: str, session_id: str, user_input: str) -> str:
    """
    Asynchronously runs the agent and returns the final response.
    """
    content = Content(role="user", parts=[Part(text=user_input)])
    final_response = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            raw = event.content.parts[0].text
            final_response = raw.strip() if isinstance(raw, str) else raw
    return final_response

def get_session_service():
    """Returns the singleton session_service instance."""
    return session_service