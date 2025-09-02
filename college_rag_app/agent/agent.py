import os
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.adk.models.lite_llm import LiteLlm
from vertexai.preview import rag
from dotenv import load_dotenv

from .prompts import return_instructions_root

load_dotenv()

# --- Environment Variable Checks ---
RAG_CORPUS = os.getenv("RAG_CORPUS")
GENAI_MODEL_NAME = os.getenv("GENAI_MODEL_NAME")

if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("WARNING: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
if not RAG_CORPUS:
    print("WARNING: RAG_CORPUS environment variable not set. RAG retrieval will fail.")
if not GENAI_MODEL_NAME:
    print("WARNING: GENAI_MODEL_NAME environment variable not set. Gemini agent will fail to load.")

# --- Tool Definition ---
ask_vertex_retrieval = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description='Use this tool to retrieve documentation and reference materials for the question from the RAG corpus.',
    rag_resources=[
        rag.RagResource(
            rag_corpus=RAG_CORPUS
        )
    ],
    similarity_top_k=7,
    vector_distance_threshold=0.6,
)

# --- Agent Factory ---
def create_rag_agent(model_instance, name: str) -> Agent:
    """Factory function to create a RAG agent with a given model."""
    return Agent(
        model=model_instance,
        name=name,
        instruction=return_instructions_root(),
        tools=[ask_vertex_retrieval]
    )

# --- Agent Definitions in a Dictionary ---
agents = {
    "gemini": create_rag_agent(
        model_instance=GENAI_MODEL_NAME,
        name='ask_rag_agent_gemini'
    ),
    "deepseek": create_rag_agent(
        model_instance=LiteLlm(model=os.getenv("DEEPSEEK_MODEL_NAME", "deepseek/DeepSeek-V2")),
        name='ask_rag_agent_deepseek'
    ),
    "openai": create_rag_agent(
        model_instance=LiteLlm(model=os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4o")),
        name='ask_rag_agent_openai'
    )
}