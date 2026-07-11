"""RAG (Retrieval-Augmented Generation) module for knowledge base."""
import os
from typing import List, Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.chains import RetrievalQA

from config import EMBEDDING_MODEL, VECTOR_STORE_DIR, NVIDIA_API_KEY, NVIDIA_BASE_URL, LLM_MODEL
from utils import logger

class RAGKnowledgeBase:
    """RAG-powered knowledge base for specialized agents."""

    def __init__(self, category: str):
        self.category = category
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store_path = VECTOR_STORE_DIR / category
        self.vector_store = None
        self.llm = None
        self.qa_chain = None

        if NVIDIA_API_KEY:
            self.llm = ChatNVIDIA(
                model=LLM_MODEL,
                api_key=NVIDIA_API_KEY,
                base_url=NVIDIA_BASE_URL,
                temperature=0.3,
                max_tokens=1024
            )

        self._load_or_create_vector_store()

    def _load_or_create_vector_store(self):
        """Load existing vector store or create new one."""
        if self.vector_store_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded vector store for {self.category}")
            except Exception as e:
                logger.warning(f"Could not load vector store: {e}")
                self.vector_store = None
        else:
            self.vector_store = None

    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to the knowledge base."""
        texts = []
        metadatas = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = {
                "title": doc.get("title", ""),
                "source": doc.get("source", ""),
                "category": self.category
            }

            # Split long documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = text_splitter.split_text(content)

            for chunk in chunks:
                texts.append(chunk)
                metadatas.append(metadata)

        if not texts:
            return

        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        else:
            self.vector_store.add_texts(texts, metadatas=metadatas)

        self.vector_store.save_local(str(self.vector_store_path))
        logger.info(f"Added {len(texts)} chunks to {self.category} knowledge base")

    def query(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant documents."""
        if self.vector_store is None:
            return []

        results = self.vector_store.similarity_search(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, "score", 0.0)
            }
            for doc in results
        ]

    def generate_response(self, query: str, context: str = "") -> str:
        """Generate a response using RAG."""
        if self.llm is None:
            return "[NVIDIA API not configured. Please set NVIDIA_API_KEY.]"

        if self.vector_store is None:
            return "[Knowledge base is empty. Please add documents first.]"

        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

            if not self.qa_chain:
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True
                )

            result = self.qa_chain.invoke({"query": query})
            return result.get("result", "Unable to generate response.")

        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return f"[Error generating response: {str(e)}]"

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if self.vector_store is None:
            return {"documents": 0, "category": self.category}

        return {
            "documents": len(self.vector_store.docstore._dict),
            "category": self.category,
            "path": str(self.vector_store_path)
        }

# Global knowledge base instances
_knowledge_bases: Dict[str, RAGKnowledgeBase] = {}

def get_knowledge_base(category: str) -> RAGKnowledgeBase:
    """Get or create a knowledge base for a category."""
    if category not in _knowledge_bases:
        _knowledge_bases[category] = RAGKnowledgeBase(category)
    return _knowledge_bases[category]
