import logging
import os
import time

from core.config import get_config_manager
from core.llm_client import create_llm_client_from_config
from agents.idea_agent import IdeaAgent
from agents.base import AgentContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_e2e_phi")

# Ensure we prefer Ollama locally (also respected by create_llm_client_from_config)
os.environ.setdefault('TERRAQORE_FORCE_OLLAMA', '1')

cfg_mgr = get_config_manager()
config = cfg_mgr.load()

# Create LLM client from config
llm_client = create_llm_client_from_config(config)
logger.info(f"Using primary provider: {llm_client.primary.model}")

# Instantiate agent with retriever if available
from core.rag_service import get_default_store
retriever = get_default_store()

agent = IdeaAgent(llm_client=llm_client, verbose=True, retriever=retriever)

context = AgentContext(
    project_id=123,
    project_name="E2E Test - Phi3.5",
    project_description="Test the E2E pipeline using local phi3.5 model",
    user_input="Generate 3 short project ideas suitable for quick prototypes."
)

start = time.time()
result = agent.execute(context)
end = time.time()

print("--- E2E RUN OUTPUT ---")
print(f"Success: {result.success}")
print(f"Execution time: {end - start:.2f}s")
print("Output (truncated 800 chars):\n")
print(result.output[:800])

if result.error:
    print("\nERROR:\n", result.error)

print("--- END ---")
