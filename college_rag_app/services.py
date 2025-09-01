import asyncio
import logging
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

# --- Import all defined agents ---
from .agent.agent import gemini_agent, deepseek_agent, openai_agent, anthropic_agent
from .config import Config
from .exceptions import AgentError

logger = logging.getLogger(__name__)

# --- Initialize a runner for each agent ---
try:
    session_service = DatabaseSessionService(db_url=Config.DATABASE_URL)
    
    runners = {
        "gemini": Runner(agent=gemini_agent, app_name=Config.APP_NAME, session_service=session_service),
        "deepseek": Runner(agent=deepseek_agent, app_name=Config.APP_NAME, session_service=session_service),
        "openai": Runner(agent=openai_agent, app_name=Config.APP_NAME, session_service=session_service),
        "anthropic": Runner(agent=anthropic_agent, app_name=Config.APP_NAME, session_service=session_service)
    }
except Exception as e:
    logger.critical(f"Failed to initialize agent services: {e}")
    raise

async def run_agent_async(user_id: str, session_id: str, user_input: str, model: str = "gemini") -> str:
    """
    Asynchronously runs the agent and returns the final response.
    Selects the agent runner based on the 'model' parameter.
    """
    runner = runners.get(model)
    if not runner:
        logger.warning(f"Invalid model '{model}' requested. Falling back to Gemini.")
        runner = runners.get("gemini")

    content = Content(role="user", parts=[Part(text=user_input)])
    final_response = ""

    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                raw = event.content.parts[0].text
                final_response = raw.strip() if isinstance(raw, str) else raw
        
        if not final_response:
             raise AgentError("Agent failed to produce a final response.")
             
        return final_response
    except Exception as e:
        logger.error(f"Error during agent execution for model {model}: {e}")
        raise AgentError(f"The selected AI model ({model}) is currently unavailable or failed to process the request.")


def get_session_service():
    """Returns the singleton session_service instance."""
    return session_service