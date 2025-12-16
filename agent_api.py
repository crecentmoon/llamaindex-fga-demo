import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import asyncio
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.client.models import ClientCheckRequest

from data import get_documents

# Load environment variables
load_dotenv()

# Configuration for Local LLM (LM Studio)
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://127.0.0.1:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "ibm/granite-4-h-tiny")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")

# Configure LlamaIndex to use the local LLM
Settings.llm = OpenAI(
    model="gpt-3.5-turbo",
    api_base=LLM_API_BASE,
    api_key=LLM_API_KEY,
)
Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

FGA_API_URL = os.getenv("FGA_API_URL", "http://localhost:8080")
FGA_STORE_ID = os.getenv("FGA_STORE_ID")

if not FGA_STORE_ID:
    raise ValueError("FGA_STORE_ID not found. Please run fga_setup.py first and set the variable.")

# Initialize OpenFGA Client Configuration
fga_config = ClientConfiguration(
    api_url=FGA_API_URL,
    store_id=FGA_STORE_ID,
)

# Global index cache
_index_cache: Optional[VectorStoreIndex] = None

def get_index() -> VectorStoreIndex:
    """Get or create the vector index."""
    global _index_cache
    if _index_cache is None:
        documents = get_documents()
        _index_cache = VectorStoreIndex.from_documents(documents)
    return _index_cache

class FGAPostprocessor(BaseNodePostprocessor):
    """Node postprocessor that filters nodes based on OpenFGA permissions."""
    
    user_id: str
    permission_results: List[Dict[str, Any]]

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self.permission_results = []

    async def _postprocess_nodes_async(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Filters nodes based on OpenFGA permissions (async version).
        """
        authorized_nodes = []
        self.permission_results = []
        
        async with OpenFgaClient(fga_config) as client:
            for node in nodes:
                doc_id = node.node.ref_doc_id
                object_str = f"document:{doc_id}"
                
                # Get document metadata
                doc_metadata = node.node.metadata or {}
                title = doc_metadata.get("title", f"Document {doc_id}")
                category = doc_metadata.get("category", "Unknown")
                
                try:
                    response = await client.check(
                        body=ClientCheckRequest(
                            user=self.user_id,
                            relation="viewer",
                            object=object_str
                        )
                    )
                    allowed = response.allowed
                    
                    # Store permission result for API response
                    self.permission_results.append({
                        "id": doc_id,
                        "title": title,
                        "category": category,
                        "allowed": allowed,
                        "score": float(node.score) if node.score else 0.0,
                        "text": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text
                    })
                    
                    if allowed:
                        authorized_nodes.append(node)
                except Exception as e:
                    # On error, deny access
                    self.permission_results.append({
                        "id": doc_id,
                        "title": title,
                        "category": category,
                        "allowed": False,
                        "score": float(node.score) if node.score else 0.0,
                        "error": str(e)
                    })
        
        return authorized_nodes

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Sync wrapper for async postprocessing.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, we need to handle this differently
                # For now, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._postprocess_nodes_async(nodes, query_bundle))
                    return future.result()
            else:
                return asyncio.run(self._postprocess_nodes_async(nodes, query_bundle))
        except RuntimeError:
            # Fallback: run in new event loop
            return asyncio.run(self._postprocess_nodes_async(nodes, query_bundle))

async def process_query(user_id: str, question: str) -> Dict[str, Any]:
    """
    Process a query with authorization checks.
    
    Returns:
        Dictionary containing:
        - answer: The AI-generated answer
        - documents: List of documents with permission results
        - allowed_count: Number of allowed documents
        - total_count: Total number of retrieved documents
    """
    import asyncio
    
    # Get index
    index = get_index()
    
    # Setup query engine with FGA postprocessor
    fga_filter = FGAPostprocessor(user_id=user_id)
    
    query_engine = index.as_query_engine(
        node_postprocessors=[fga_filter],
        similarity_top_k=5
    )
    
    # Query (LlamaIndex query is synchronous, so we run it in executor)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: query_engine.query(question)
    )
    
    # Get permission results from postprocessor
    documents = fga_filter.permission_results
    allowed_count = sum(1 for doc in documents if doc.get("allowed", False))
    total_count = len(documents)
    
    return {
        "answer": str(response),
        "documents": documents,
        "allowed_count": allowed_count,
        "total_count": total_count
    }

