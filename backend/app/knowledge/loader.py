"""
Knowledge Loader — ingests documents using LlamaIndex.
"""
from pathlib import Path
from loguru import logger
from typing import List

try:
    from llama_index.core import SimpleDirectoryReader, Document
    HAS_LLAMA_INDEX = True
except ImportError:
    HAS_LLAMA_INDEX = False
    Document = dict


class KnowledgeLoader:
    def __init__(self, data_dir: str = "./data/knowledge"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_documents(self) -> List[Document]:
        """Load all documents from the knowledge directory."""
        if not HAS_LLAMA_INDEX:
            logger.warning("LlamaIndex not installed. Cannot load documents.")
            return []
            
        logger.info(f"Loading documents from {self.data_dir}")
        try:
            reader = SimpleDirectoryReader(str(self.data_dir), recursive=True)
            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents.")
            return documents
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return []
