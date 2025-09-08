class AgentError(Exception):
    """Custom exception for errors related to the AI agent or LLM service."""
    pass

class ExternalApiError(Exception):
    """Custom exception for errors related to external services (like embedding APIs)."""
    pass