import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
import asyncio
import argparse
from typing import List, Optional
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.credentials import Credentials
from openfga_sdk.client.models import ClientCheckRequest

from data import get_documents

# Load environment variables
load_dotenv()

# Configuration for Local LLM (LM Studio)
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://127.0.0.1:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "ibm/granite-4-h-tiny")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio") # Dummy key for local

# Configure LlamaIndex to use the local LLM
# We use "gpt-3.5-turbo" as the model name to satisfy LlamaIndex's validation,
# but the request is sent to the local LM Studio server (LLM_API_BASE).
Settings.llm = OpenAI(
    model="gpt-3.5-turbo",
    api_base=LLM_API_BASE,
    api_key=LLM_API_KEY,
)
Settings.embed_model = "local:BAAI/bge-small-en-v1.5" # Use a local embedding model to avoid OpenAI calls completely

FGA_API_URL = os.getenv("FGA_API_URL", "http://localhost:8080")
FGA_STORE_ID = os.getenv("FGA_STORE_ID")

if not FGA_STORE_ID:
    print("Error: FGA_STORE_ID not found. Please run fga_setup.py first and set the variable.")
    sys.exit(1)

# Initialize OpenFGA Client
fga_config = ClientConfiguration(
    api_url=FGA_API_URL,
    store_id=FGA_STORE_ID,
)

# Define the Node Postprocessor for Authorization
class FGAPostprocessor(BaseNodePostprocessor):
    user_id: str

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Filters nodes based on OpenFGA permissions.
        """
        authorized_nodes = []
        
        # We need to run async checks. 
        # Since this method is sync, we'll run the loop here or use the sync client if available.
        # The OpenFGA Python SDK 'OpenFgaClient' methods are coroutines.
        # We will use a helper to run them.
        
        print(f"\n[FGA] Checking permissions for user: {self.user_id}")
        
        async def check_permissions():
            results = []
            async with OpenFgaClient(fga_config) as client:
                for node in nodes:
                    doc_id = node.node.ref_doc_id
                    # Our doc_ids in data.py are now like "engineering_roadmap"
                    # OpenFGA expects "document:engineering_roadmap"
                    object_str = f"document:{doc_id}"
                    


                    try:
                        response = await client.check(
                            body=ClientCheckRequest(
                                user=self.user_id,
                                relation="viewer",
                                object=object_str
                            )
                        )
                        allowed = response.allowed
                        print(f"  - Checking {object_str} -> {'ALLOWED' if allowed else 'DENIED'}")
                        if allowed:
                            results.append(node)
                    except Exception as e:
                        print(f"  - Error checking {object_str}: {e}")
            return results

        try:
            authorized_nodes = asyncio.run(check_permissions())
        except RuntimeError:
            # If we are already in an event loop (e.g. jupyter), this might fail.
            # But for a script, asyncio.run is fine.
            pass
            
        return authorized_nodes

def main():
    parser = argparse.ArgumentParser(description="Secure AI Agent Demo")
    parser.add_argument("--user", type=str, required=True, help="User ID (e.g., user:alice)")
    parser.add_argument("--question", type=str, required=True, help="Question to ask")
    args = parser.parse_args()

    user_id = args.user
    question = args.question

    print(f"--- Starting Agent for {user_id} ---")
    
    # 1. Load Data
    documents = get_documents()
    
    # 2. Index Data
    # In a real app, you'd load the index from disk.
    print("Indexing documents...")
    index = VectorStoreIndex.from_documents(documents)
    
    # 3. Setup Query Engine with FGA Postprocessor
    fga_filter = FGAPostprocessor(user_id=user_id)
    
    query_engine = index.as_query_engine(
        node_postprocessors=[fga_filter],
        similarity_top_k=5
    )
    
    # 4. Query
    print(f"Question: {question}")
    response = query_engine.query(question)
    
    print("\n--- Response ---")
    print(response)
    print("----------------")

if __name__ == "__main__":
    main()
