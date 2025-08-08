"""
MCP Ingestion Agent
Handles document parsing and processing
"""

import logging
import time
import os
from typing import Dict, Any, Optional
from utils.mcp_client import MCPAgent
from utils.mcp import MessageType
from utils.document_parser import DocumentParser

logger = logging.getLogger(__name__)

class MCPIngestionAgent(MCPAgent):
    """Agent responsible for document ingestion and parsing"""
    
    def __init__(self, api_url: Optional[str] = None):
        super().__init__("IngestionAgent", api_url)
        
        # Initialize document parser
        self.parser = DocumentParser()
        
        # Enhanced stats
        self.stats.update({
            "documents_processed": 0,
            "chunks_created": 0,
            "processing_errors": 0,
            "total_processing_time": 0.0
        })
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("MCP Ingestion Agent initialized")
    
    def _register_handlers(self):
        """Register message handlers"""
        self.mcp.register_handler(MessageType.INGESTION_REQUEST.value, self.handle_ingestion_request)
    
    def handle_ingestion_request(self, message):
        """Handle document ingestion requests"""
        try:
            file_path = message.payload.get("file_path")
            chunk_size = message.payload.get("chunk_size", 1000)
            chunk_overlap = message.payload.get("chunk_overlap", 200)
            
            if not file_path:
                self.mcp.send_error(message.sender, "No file_path provided")
                return
            
            if not os.path.exists(file_path):
                self.mcp.send_error(message.sender, f"File not found: {file_path}")
                return
            
            logger.info(f"Processing document: {file_path}")
            start_time = time.time()
            
            # Parse the document
            chunks = self.parser.parse_file(file_path, chunk_size, chunk_overlap)
            
            processing_time = time.time() - start_time
            
            if not chunks:
                self.mcp.send_error(message.sender, f"No content extracted from {file_path}")
                return
            
            # Update stats
            self.stats["documents_processed"] += 1
            self.stats["chunks_created"] += len(chunks)
            self.stats["total_processing_time"] += processing_time
            
            # Send processed chunks to retrieval agent for indexing
            self.mcp.send(
                receiver="RetrievalAgent",
                msg_type=MessageType.DOCUMENT_PROCESSED.value,
                payload={
                    "file_path": file_path,
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                    "processing_time": processing_time,
                    "metadata": {
                        "filename": os.path.basename(file_path),
                        "file_size": os.path.getsize(file_path),
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                },
                trace_id=message.trace_id,
                workflow_id=message.workflow_id
            )
            
            logger.info(f"Document processed: {file_path} -> {len(chunks)} chunks in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats["processing_errors"] += 1
            self.mcp.send_error(message.sender, error_msg)
    
    def process_document(self, file_path: str, chunk_size: int = 1000, 
                        chunk_overlap: int = 200) -> Dict[str, Any]:
        """Process a document (direct method)"""
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "error": f"File not found: {file_path}"}
            
            start_time = time.time()
            chunks = self.parser.parse_file(file_path, chunk_size, chunk_overlap)
            processing_time = time.time() - start_time
            
            if not chunks:
                return {"status": "error", "error": f"No content extracted from {file_path}"}
            
            # Update stats
            self.stats["documents_processed"] += 1
            self.stats["chunks_created"] += len(chunks)
            self.stats["total_processing_time"] += processing_time
            
            return {
                "status": "success",
                "file_path": file_path,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "processing_time": processing_time,
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                }
            }
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats["processing_errors"] += 1
            return {"status": "error", "error": error_msg}