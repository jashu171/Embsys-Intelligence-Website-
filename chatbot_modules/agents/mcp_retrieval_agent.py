"""
MCP Retrieval Agent
Handles vector storage and document retrieval
"""

import logging
import time
from typing import Dict, Any, Optional, List
from utils.mcp_client import MCPAgent
from utils.mcp import MessageType
from utils.vector_store import VectorStore
from config import config

logger = logging.getLogger(__name__)

class MCPRetrievalAgent(MCPAgent):
    """Agent responsible for document storage and retrieval"""
    
    def __init__(self, api_url: Optional[str] = None):
        super().__init__("RetrievalAgent", api_url)
        
        # Initialize vector store
        try:
            self.vector_store = VectorStore(
                collection_name=config.agent.collection_name,
                persist_directory=config.agent.persist_directory,
                embedding_model=config.agent.embedding_model
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
        
        # Enhanced stats
        self.stats.update({
            "documents_indexed": 0,
            "chunks_stored": 0,
            "queries_processed": 0,
            "total_retrieval_time": 0.0,
            "average_retrieval_time": 0.0
        })
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("MCP Retrieval Agent initialized")
    
    def _register_handlers(self):
        """Register message handlers"""
        self.mcp.register_handler(MessageType.DOCUMENT_PROCESSED.value, self.handle_document_processed)
        self.mcp.register_handler(MessageType.QUERY_REQUEST.value, self.handle_query_request)
    
    def handle_document_processed(self, message):
        """Handle processed documents from ingestion agent"""
        try:
            file_path = message.payload.get("file_path")
            chunks = message.payload.get("chunks", [])
            metadata = message.payload.get("metadata", {})
            
            if not chunks:
                self.mcp.send_error(message.sender, "No chunks provided for indexing")
                return
            
            logger.info(f"Indexing {len(chunks)} chunks from {file_path}")
            start_time = time.time()
            
            # Prepare metadata for each chunk
            chunk_metadatas = []
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **metadata,
                    "source_file": file_path,
                    "chunk_index": i,
                    "chunk_type": "text",
                    "word_count": len(chunk.split()),
                    "char_count": len(chunk)
                }
                chunk_metadatas.append(chunk_metadata)
                chunk_ids.append(f"{file_path}_{i}")
            
            # Add to vector store
            result = self.vector_store.add_documents(
                texts=chunks,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            
            indexing_time = time.time() - start_time
            
            if result["status"] == "error":
                self.mcp.send_error(message.sender, f"Indexing failed: {result['error']}")
                return
            
            # Update stats
            self.stats["documents_indexed"] += 1
            self.stats["chunks_stored"] += len(chunks)
            
            # Send success response
            self.mcp.send(
                receiver="CoordinatorAgent",
                msg_type=MessageType.DOCUMENTS_INDEXED.value,
                payload={
                    "file_path": file_path,
                    "chunks_indexed": len(chunks),
                    "indexing_time": indexing_time,
                    "collection_size": result.get("collection_size", 0),
                    "status": "success"
                },
                trace_id=message.trace_id,
                workflow_id=message.workflow_id
            )
            
            logger.info(f"Indexed {len(chunks)} chunks from {file_path} in {indexing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Error indexing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.mcp.send_error(message.sender, error_msg)
    
    def handle_query_request(self, message):
        """Handle query requests"""
        try:
            query = message.payload.get("query")
            search_k = message.payload.get("search_k", config.agent.default_search_k)
            similarity_threshold = message.payload.get("similarity_threshold", config.agent.similarity_threshold)
            
            if not query:
                self.mcp.send_error(message.sender, "No query provided")
                return
            
            logger.info(f"Processing query: {query[:50]}...")
            start_time = time.time()
            
            # Search vector store
            search_result = self.vector_store.search(
                query=query,
                k=search_k,
                similarity_threshold=similarity_threshold
            )
            
            retrieval_time = time.time() - start_time
            
            if search_result["status"] == "error":
                self.mcp.send_error(message.sender, f"Search failed: {search_result['error']}")
                return
            
            # Update stats
            self.stats["queries_processed"] += 1
            self.stats["total_retrieval_time"] += retrieval_time
            self._update_average_retrieval_time()
            
            # Send context to LLM agent
            self.mcp.send(
                receiver="LLMResponseAgent",
                msg_type=MessageType.CONTEXT_RESPONSE.value,
                payload={
                    "query": query,
                    "retrieved_context": search_result["top_chunks"],
                    "chunk_metadata": search_result["chunk_metadata"],
                    "similarity_scores": search_result["similarity_scores"],
                    "collection_size": search_result["collection_size"],
                    "retrieval_time": retrieval_time
                },
                trace_id=message.trace_id,
                workflow_id=message.workflow_id
            )
            
            logger.info(f"Retrieved {len(search_result['top_chunks'])} chunks for query in {retrieval_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.mcp.send_error(message.sender, error_msg)
    
    def _update_average_retrieval_time(self):
        """Update average retrieval time"""
        if self.stats["queries_processed"] > 0:
            self.stats["average_retrieval_time"] = (
                self.stats["total_retrieval_time"] / self.stats["queries_processed"]
            )
    
    def retrieve_context(self, query: str, k: int = 5, 
                        similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Retrieve context for a query (direct method)"""
        try:
            start_time = time.time()
            
            search_result = self.vector_store.search(
                query=query,
                k=k,
                similarity_threshold=similarity_threshold
            )
            
            retrieval_time = time.time() - start_time
            
            # Update stats
            self.stats["queries_processed"] += 1
            self.stats["total_retrieval_time"] += retrieval_time
            self._update_average_retrieval_time()
            
            if search_result["status"] == "error":
                return search_result
            
            return {
                "status": "success",
                "top_chunks": search_result["top_chunks"],
                "chunk_metadata": search_result["chunk_metadata"],
                "similarity_scores": search_result["similarity_scores"],
                "collection_size": search_result["collection_size"],
                "retrieval_time": retrieval_time
            }
            
        except Exception as e:
            error_msg = f"Error retrieving context: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the vector store"""
        try:
            result = self.vector_store.clear_collection()
            
            if result["status"] == "success":
                # Reset stats
                self.stats["documents_indexed"] = 0
                self.stats["chunks_stored"] = 0
                logger.info("Vector store cleared successfully")
            
            return result
            
        except Exception as e:
            error_msg = f"Error clearing collection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        return self.vector_store.get_collection_info()