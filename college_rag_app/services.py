import asyncio
import logging
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

from .agent.agent import agents
from .config import Config
from .exceptions import AgentError

logger = logging.getLogger(__name__)

# --- Initialize a runner for each agent ---
try:
    session_service = DatabaseSessionService(db_url=Config.DATABASE_URL)
    
    # Use a dictionary comprehension for cleaner initialization
    runners = {
        name: Runner(agent=agent, app_name=Config.APP_NAME, session_service=session_service)
        for name, agent in agents.items()
    }

except Exception as e:
    logger.critical(f"Failed to initialize agent services: {e}")
    raise

async def run_agent_async(user_id: str, session_id: str, user_input: str, model: str = "gemini") -> str:
    """
    Asynchronously runs the agent and returns the final response.
    Selects the agent runner based on the 'model' parameter.
    """
    # Use .get() with a default value for cleaner fallback logic
    runner = runners.get(model)
    if not runner:
        logger.warning(f"Invalid model '{model}' requested. Falling back to Gemini.")
        runner = runners["gemini"] # Direct access since 'gemini' should always exist

    content = Content(role="user", parts=[Part(text=user_input)])
    final_response = ""

    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                part = event.content.parts[0]
                if hasattr(part, 'text'):
                    final_response = part.text.strip()
        
        if not final_response:
             raise AgentError("Agent failed to produce a final response.")
             
        return final_response
    except Exception as e:
        logger.error(f"Error during agent execution for model {model}: {e}", exc_info=True) # Added exc_info
        raise AgentError(f"The selected AI model ({model}) is currently unavailable or failed to process the request.")

def get_session_service():
    """Returns the singleton session_service instance."""
    return session_service