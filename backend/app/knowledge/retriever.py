"""
Knowledge Retriever — retrieves info from the knowledge base.
"""
from typing import List
from loguru import logger

try:
    from llama_index.core import VectorStoreIndex
    HAS_LLAMA_INDEX = True
except ImportError:
    HAS_LLAMA_INDEX = False

class KnowledgeRetriever:
    def __init__(self, documents: List = None):
        self.index = None
        
        if not HAS_LLAMA_INDEX:
            logger.warning("LlamaIndex not installed. Retriever disabled.")
            return
            
        if documents:
            logger.info(f"Building Knowledge Index from {len(documents)} documents.")
            try:
                self.index = VectorStoreIndex.from_documents(documents)
            except Exception as e:
                logger.error(f"Failed to build index: {e}")
                
    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant knowledge snippets."""
        if not self.index:
            return []
            
        try:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            return [node.get_content() for node in nodes]
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge: {e}")
            return []
