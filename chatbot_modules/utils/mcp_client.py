"""
MCP Client Base Class
"""

import logging
import time
from typing import Dict, Any, Optional
from .mcp import MCP, broker

logger = logging.getLogger(__name__)

class MCPAgent:
    """Base class for MCP-enabled agents"""
    
    def __init__(self, agent_id: str, api_url: Optional[str] = None):
        self.agent_id = agent_id
        self.api_url = api_url
        self.mcp = MCP(agent_id)
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "uptime_start": time.time()
        }
        
        # Register basic handlers
        self._register_base_handlers()
    
    def _register_base_handlers(self):
        """Register base message handlers"""
        from .mcp import MessageType
        self.mcp.register_handler(MessageType.HEALTH_CHECK.value, self._handle_health_check)
    
    def _handle_health_check(self, message):
        """Handle health check requests"""
        health_info = self.health_check()
        self.mcp.reply_to(
            original_msg=message,
            msg_type="HEALTH_RESPONSE",
            payload=health_info
        )
    
    def send_message(self, receiver: str, msg_type: str, payload: Dict[str, Any], 
                    trace_id: str = None, priority: str = "MEDIUM", 
                    workflow_id: str = None):
        """Send a message via MCP"""
        self.stats["messages_sent"] += 1
        return self.mcp.send(
            receiver=receiver,
            msg_type=msg_type,
            payload=payload,
            trace_id=trace_id,
            priority=priority,
            workflow_id=workflow_id
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Get agent health status"""
        uptime = time.time() - self.stats["uptime_start"]
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "uptime_seconds": uptime,
            "stats": self.get_stats(),
            "timestamp": time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            "uptime_seconds": time.time() - self.stats["uptime_start"]
        }