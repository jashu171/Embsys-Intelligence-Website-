"""
Simple Vector Store Implementation using ChromaDB with built-in embeddings
"""

import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """ChromaDB-based vector store with built-in embeddings"""
    
    def __init__(self, collection_name: str = "document_store", 
                 persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Create persist directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with built-in embedding function
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection with default embedding function
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            # Create collection with default embedding function
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Document embeddings for RAG system"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None,
                     ids: List[str] = None) -> Dict[str, Any]:
        """Add documents to the vector store"""
        try:
            if not texts:
                return {"status": "error", "error": "No texts provided"}
            
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in texts]
            
            # Prepare metadatas
            if metadatas is None:
                metadatas = [{"source": "unknown"} for _ in texts]
            
            # Add to collection (ChromaDB will handle embeddings automatically)
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to vector store")
            
            return {
                "status": "success",
                "documents_added": len(texts),
                "collection_size": self.collection.count()
            }
            
        except Exception as e:
            error_msg = f"Error adding documents to vector store: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def search(self, query: str, k: int = 5, 
               similarity_threshold: float = 0.0) -> Dict[str, Any]:
        """Search for similar documents"""
        try:
            if not query.strip():
                return {"status": "error", "error": "Empty query provided"}
            
            # Search in collection (ChromaDB handles query embedding automatically)
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["documents"] or not results["documents"][0]:
                return {
                    "status": "success",
                    "top_chunks": [],
                    "chunk_metadata": [],
                    "similarity_scores": [],
                    "collection_size": self.collection.count()
                }
            
            # Process results
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            # Convert distances to similarity scores (1 - distance)
            similarity_scores = [max(0, 1 - dist) for dist in distances]
            
            # Filter by similarity threshold
            filtered_results = []
            filtered_metadata = []
            filtered_scores = []
            
            # Debug: Log all scores before filtering
            logger.info(f"Raw similarity scores before filtering: {similarity_scores}")
            logger.info(f"Similarity threshold: {similarity_threshold}")
            
            for i, (doc, metadata, score) in enumerate(zip(documents, metadatas, similarity_scores)):
                if score >= similarity_threshold:
                    filtered_results.append(doc)
                    filtered_metadata.append(metadata or {})
                    filtered_scores.append(score)
            
            logger.info(f"Search returned {len(filtered_results)} results for query: {query[:50]}...")
            
            return {
                "status": "success",
                "top_chunks": filtered_results,
                "chunk_metadata": filtered_metadata,
                "similarity_scores": filtered_scores,
                "collection_size": self.collection.count()
            }
            
        except Exception as e:
            error_msg = f"Error searching vector store: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the collection"""
        try:
            # Delete the collection
            self.client.delete_collection(self.collection_name)
            
            # Recreate the collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Document embeddings for RAG system"}
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            
            return {
                "status": "success",
                "message": "Collection cleared successfully"
            }
            
        except Exception as e:
            error_msg = f"Error clearing collection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "status": "success",
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": "chromadb_default",
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            error_msg = f"Error getting collection info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}