import os
import asyncio
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



def _get_sync_embedding(query: str) -> list[float] | None:
    """
    Synchronous helper to run the blocking genai embedding call in a thread.
    """
    logger.info("Executing synchronous embedding generation in thread pool...")
    try:
        embed_result = genai.embed_content(
            model=Config.EMBEDDING_MODEL_NAME,
            content=query,
            task_type="retrieval_query"
        )
        return embed_result['embedding']
    except Exception as e:
        logger.error(f"Error during synchronous embedding generation: {e}", exc_info=True)
        return None 



def _execute_db_query(sql_query: text, query_vector: list[float]) -> list[str]:
    """
    Synchronous helper to run the blocking DB query in a separate thread.
    """
    logger.info("Executing synchronous DB query in thread pool...")
    try:
        with db.engine.connect() as conn:
            results = conn.execute(sql_query, {"query_vec": str(query_vector)})
            context_chunks = [row[0] for row in results.fetchall()]
        logger.info(f"DB query thread pool task finished, found {len(context_chunks)} chunks.")
        return context_chunks
    except Exception as e:
        logger.error(f"Error during synchronous DB query execution: {e}", exc_info=True)
        return []


async def retrieve_pgvector_documents(query: str) -> dict:
    """
    (Async) Retrieves relevant document chunks from the pgvector database based on a user query.
    This function runs both blocking I/O calls (embedding and DB query) in separate threads.
    """
    logger.info(f"Async Tool executing: retrieve_pgvector_documents with query: '{query}'")
    try:
        query_vector = await asyncio.to_thread(_get_sync_embedding, query)

        if query_vector is None:
            raise Exception("Embedding generation failed. Check error logs.")

        sql_query = text(
            f"""
            SELECT {Config.PG_CONTENT_COLUMN} 
            FROM {Config.PG_TABLE_NAME}
            ORDER BY {Config.PG_VECTOR_COLUMN} <=> :query_vec 
            LIMIT 6
            """
        )
        
        context_chunks = await asyncio.to_thread(
            _execute_db_query, sql_query, query_vector
        )

        if not context_chunks:
            logger.warning("PGVector tool ran but found no matching documents.")
            return {"status": "success", "retrieved_context": "No information found."}

        context = "\n---\n".join(context_chunks)
        logger.info(f"Async Tool success: Retrieved {len(context_chunks)} chunks.")
        
        return {
            "status": "success",
            "retrieved_context": context
        }

    except Exception as e:
        logger.error(f"Error in async retrieve_pgvector_documents tool: {e}", exc_info=True)
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