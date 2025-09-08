# file: agent/agent.py
import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import logging
from sqlalchemy import text
import google.generativeai as genai
from .config import Config
from .prompts import return_instructions_root
from .models import db

load_dotenv()
logger = logging.getLogger('app')

# --- Environment Variable Checks ---
GENAI_MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME")

if not GENAI_MODEL_NAME:
    print("WARNING: GENAI_MODEL_NAME environment variable not set. Gemini agent will fail to load.")
if not Config.GOOGLE_API_KEY:
     print("WARNING: GOOGLE_API_KEY not set in Config. Embedding and Chat will fail.")


def retrieve_pgvector_documents(query: str) -> dict:
    """
    Retrieves relevant document chunks from the pgvector database based on a user query.

    Args:
        query (str): The specific user question about college admissions or policies.
    """
    logger.info(f"Tool executing: retrieve_pgvector_documents with query: '{query}'")
    try:
        # 1. Generate an embedding for the user's query
        embed_result = genai.embed_content(
            model=Config.EMBEDDING_MODEL_NAME,
            content=query,
            task_type="retrieval_query"
        )
        query_vector = embed_result['embedding']

        sql_query = text(
            f"""
            SELECT {Config.PG_CONTENT_COLUMN} 
            FROM {Config.PG_TABLE_NAME}
            ORDER BY {Config.PG_VECTOR_COLUMN} <=> :query_vec 
            LIMIT 6
            """
        )

        with db.engine.connect() as conn:
            results = conn.execute(sql_query, {"query_vec": str(query_vector)})
            context_chunks = [row[0] for row in results.fetchall()]

        if not context_chunks:
            logger.warning("PGVector tool ran but found no matching documents.")
            return {"status": "success", "retrieved_context": "No information found."}

        context = "\n---\n".join(context_chunks)
        logger.info(f"Tool success: Retrieved {len(context_chunks)} chunks.")
        
        return {
            "status": "success",
            "retrieved_context": context
        }

    except Exception as e:
        logger.error(f"Error in retrieve_pgvector_documents tool: {e}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"An error occurred while trying to retrieve documents: {e}"
        }


def create_rag_agent(model_instance, name: str) -> Agent:
    """Factory function to create a RAG agent with a given model."""
    return Agent(
        model=model_instance,
        name=name,
        instruction=return_instructions_root(),
        tools=[retrieve_pgvector_documents]  
    )


agents = {
    "gemini": create_rag_agent(
        model_instance=GENAI_MODEL_NAME,
        name='ask_rag_agent_gemini'
    ),
    "openai": create_rag_agent(
        model_instance=LiteLlm(model=os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4o")),
        name='ask_rag_agent_openai'
    )
}