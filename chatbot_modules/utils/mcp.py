"""
Model Context Protocol (MCP) Implementation
Simplified version for the chatbot system
"""

import logging
import time
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """MCP Message types"""
    # Document processing
    INGESTION_REQUEST = "INGESTION_REQUEST"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    DOCUMENTS_INDEXED = "DOCUMENTS_INDEXED"
    
    # Query processing
    QUERY_REQUEST = "QUERY_REQUEST"
    CONTEXT_RESPONSE = "CONTEXT_RESPONSE"
    RESPONSE_GENERATED = "RESPONSE_GENERATED"
    
    # System messages
    HEALTH_CHECK = "HEALTH_CHECK"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    ERROR = "ERROR"
    
    # Workflow management
    WORKFLOW_START = "WORKFLOW_START"
    WORKFLOW_COMPLETE = "WORKFLOW_COMPLETE"

@dataclass
class MCPMessage:
    """MCP Message structure"""
    sender: str
    receiver: str
    msg_type: str
    trace_id: str
    payload: Dict[str, Any]
    timestamp: float
    priority: str = "MEDIUM"
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    workflow_id: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_error(self) -> bool:
        """Check if message contains an error"""
        return self.error is not None or self.msg_type == MessageType.ERROR.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return asdict(self)

class MCPBroker:
    """Simple MCP message broker for in-memory communication"""
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Dict[str, Callable]] = {}
        self.message_history: List[MCPMessage] = []
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "agents_registered": 0
        }
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        """Register an agent with the broker"""
        self.agents[agent_id] = {
            **agent_info,
            "registered_at": time.time(),
            "last_seen": time.time()
        }
        self.stats["agents_registered"] += 1
        logger.info(f"Agent registered: {agent_id}")
    
    def register_handler(self, agent_id: str, message_type: str, handler: Callable):
        """Register a message handler for an agent"""
        if agent_id not in self.message_handlers:
            self.message_handlers[agent_id] = {}
        self.message_handlers[agent_id][message_type] = handler
        logger.debug(f"Handler registered: {agent_id} -> {message_type}")
    
    def send_message(self, message: MCPMessage) -> bool:
        """Send a message through the broker"""
        try:
            # Add to history
            self.message_history.append(message)
            self.stats["messages_sent"] += 1
            
            # Update sender's last seen
            if message.sender in self.agents:
                self.agents[message.sender]["last_seen"] = time.time()
            
            # Route message to handler
            if message.receiver in self.message_handlers:
                handlers = self.message_handlers[message.receiver]
                if message.msg_type in handlers:
                    try:
                        handlers[message.msg_type](message)
                        self.stats["messages_received"] += 1
                        return True
                    except Exception as e:
                        logger.error(f"Handler error for {message.msg_type}: {str(e)}")
                        self.stats["errors"] += 1
                        return False
            
            # If no specific handler, try broadcast
            if message.receiver == "*":
                success_count = 0
                for agent_id, handlers in self.message_handlers.items():
                    if message.msg_type in handlers:
                        try:
                            handlers[message.msg_type](message)
                            success_count += 1
                        except Exception as e:
                            logger.error(f"Broadcast handler error for {agent_id}: {str(e)}")
                
                if success_count > 0:
                    self.stats["messages_received"] += success_count
                    return True
            
            logger.warning(f"No handler found for message: {message.receiver} -> {message.msg_type}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.stats["errors"] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics"""
        return {
            **self.stats,
            "active_agents": len(self.agents),
            "message_history_size": len(self.message_history),
            "timestamp": time.time()
        }
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agents"""
        return list(self.agents.keys())
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages"""
        recent = self.message_history[-limit:] if self.message_history else []
        return [msg.to_dict() for msg in recent]
    
    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        logger.info("Message history cleared")

# Global broker instance
broker = MCPBroker()

class MCP:
    """MCP client for agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.handlers[message_type] = handler
        broker.register_handler(self.agent_id, message_type, handler)
    
    def send(self, receiver: str, msg_type: str, payload: Dict[str, Any], 
             trace_id: str = None, priority: str = "MEDIUM", 
             workflow_id: str = None) -> MCPMessage:
        """Send a message"""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        message = MCPMessage(
            sender=self.agent_id,
            receiver=receiver,
            msg_type=msg_type,
            trace_id=trace_id,
            payload=payload,
            timestamp=time.time(),
            priority=priority,
            workflow_id=workflow_id
        )
        
        broker.send_message(message)
        return message
    
    def send_error(self, receiver: str, error_msg: str, trace_id: str = None):
        """Send an error message"""
        return self.send(
            receiver=receiver,
            msg_type=MessageType.ERROR.value,
            payload={"error": error_msg},
            trace_id=trace_id
        )
    
    def reply_to(self, original_msg: MCPMessage, msg_type: str, payload: Dict[str, Any]):
        """Reply to a message"""
        return self.send(
            receiver=original_msg.sender,
            msg_type=msg_type,
            payload=payload,
            trace_id=original_msg.trace_id,
            workflow_id=original_msg.workflow_id
        )