"""
MCP LLM Agent
Handles response generation using Google Gemini
"""

import logging
import time
import os
from typing import Dict, Any, Optional, List
from utils.mcp_client import MCPAgent
from utils.mcp import MessageType
from config import config

logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not available - LLM functionality will be limited")

class MCPLLMAgent(MCPAgent):
    """Agent responsible for generating responses using LLM"""
    
    def __init__(self, api_url: Optional[str] = None):
        super().__init__("LLMResponseAgent", api_url)
        
        # Initialize Gemini client
        self.model = None
        if GENAI_AVAILABLE:
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(config.agent.model_name)
                    logger.info(f"Gemini model initialized: {config.agent.model_name}")
                else:
                    logger.warning("GEMINI_API_KEY not found in environment")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {str(e)}")
        
        # Enhanced stats
        self.stats.update({
            "responses_generated": 0,
            "total_generation_time": 0.0,
            "average_generation_time": 0.0,
            "generation_errors": 0,
            "total_tokens_used": 0
        })
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("MCP LLM Agent initialized")
    
    def _register_handlers(self):
        """Register message handlers"""
        self.mcp.register_handler(MessageType.CONTEXT_RESPONSE.value, self.handle_context_response)
    
    def handle_context_response(self, message):
        """Handle context from retrieval agent and generate response"""
        try:
            query = message.payload.get("query")
            context_chunks = message.payload.get("retrieved_context", [])
            chunk_metadata = message.payload.get("chunk_metadata", [])
            similarity_scores = message.payload.get("similarity_scores", [])
            
            if not query:
                self.mcp.send_error(message.sender, "No query provided")
                return
            
            logger.info(f"Generating response for query: {query[:50]}...")
            start_time = time.time()
            
            # Generate response
            response_result = self._generate_response(query, context_chunks, chunk_metadata)
            
            generation_time = time.time() - start_time
            
            if response_result["status"] == "error":
                self.mcp.send_error(message.sender, f"Response generation failed: {response_result['error']}")
                return
            
            # Update stats
            self.stats["responses_generated"] += 1
            self.stats["total_generation_time"] += generation_time
            self._update_average_generation_time()
            
            # Send response to coordinator
            self.mcp.send(
                receiver="CoordinatorAgent",
                msg_type=MessageType.RESPONSE_GENERATED.value,
                payload={
                    "query": query,
                    "answer": response_result["answer"],
                    "response_type": response_result["response_type"],
                    "context_used": len(context_chunks),
                    "generation_time": generation_time,
                    "similarity_scores": similarity_scores,
                    "status": "success"
                },
                trace_id=message.trace_id,
                workflow_id=message.workflow_id
            )
            
            logger.info(f"Response generated in {generation_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats["generation_errors"] += 1
            self.mcp.send_error(message.sender, error_msg)
    
    def _generate_response(self, query: str, context_chunks: List[str], 
                          chunk_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using context"""
        try:
            if not self.model:
                # Fallback response when Gemini is not available
                if context_chunks:
                    return {
                        "status": "success",
                        "answer": f"Based on the uploaded documents, I found relevant information about your query: '{query}'. However, the AI model is not fully configured. Please check your GEMINI_API_KEY environment variable.",
                        "response_type": "fallback"
                    }
                else:
                    return {
                        "status": "success",
                        "answer": f"I received your query: '{query}'. However, no relevant documents were found and the AI model is not fully configured. Please upload some documents and check your GEMINI_API_KEY environment variable.",
                        "response_type": "fallback"
                    }
            
            # Prepare context
            if context_chunks:
                context_text = "\n\n".join([f"Context {i+1}: {chunk}" for i, chunk in enumerate(context_chunks[:5])])
                
                prompt = f"""Based on the following context from uploaded documents, please answer the user's question.

Context:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please say so and provide what information you can from the context."""
            else:
                prompt = f"""The user asked: {query}

No relevant documents were found in the knowledge base. Please provide a helpful general response and suggest that the user upload relevant documents for more specific information."""
            
            # Generate response using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config.agent.max_tokens,
                    temperature=config.agent.temperature,
                )
            )
            
            if response.text:
                return {
                    "status": "success",
                    "answer": response.text.strip(),
                    "response_type": "rag" if context_chunks else "general"
                }
            else:
                return {
                    "status": "error",
                    "error": "No response generated by the model"
                }
                
        except Exception as e:
            error_msg = f"Error in response generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def _update_average_generation_time(self):
        """Update average generation time"""
        if self.stats["responses_generated"] > 0:
            self.stats["average_generation_time"] = (
                self.stats["total_generation_time"] / self.stats["responses_generated"]
            )
    
    def generate_response(self, query: str, context_chunks: List[str], 
                         chunk_metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response (direct method)"""
        try:
            start_time = time.time()
            
            if chunk_metadata is None:
                chunk_metadata = []
            
            response_result = self._generate_response(query, context_chunks, chunk_metadata)
            
            generation_time = time.time() - start_time
            
            # Update stats
            self.stats["responses_generated"] += 1
            self.stats["total_generation_time"] += generation_time
            self._update_average_generation_time()
            
            if response_result["status"] == "error":
                self.stats["generation_errors"] += 1
                return response_result
            
            return {
                **response_result,
                "generation_time": generation_time,
                "context_used": len(context_chunks)
            }
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats["generation_errors"] += 1
            return {"status": "error", "error": error_msg}