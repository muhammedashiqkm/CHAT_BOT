import os
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from dotenv import load_dotenv


from .prompts import return_instructions_root


GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not GOOGLE_APPLICATION_CREDENTIALS:
    print("WARNING: GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Agent might not work.")

ask_vertex_retrieval = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description=(
        'Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,'
    ),
    rag_resources=[
        rag.RagResource(
            rag_corpus=os.environ.get("RAG_CORPUS")
        )
    ],
    similarity_top_k=6,
    vector_distance_threshold=0.6,
)

root_agent = Agent(
    model=os.environ.get("GENAI_MODEL_NAME"),
    name='ask_rag_agent',
    instruction=return_instructions_root(),
    tools=[
        ask_vertex_retrieval,
    ]
)

if not os.getenv("RAG_CORPUS"):
    print("WARNING: RAG_CORPUS environment variable not set. RAG retrieval might not function.")
if not os.getenv("GENAI_MODEL_NAME"):
    print("WARNING: GENAI_MODEL_NAME environment variable not set. Agent model might not load.")