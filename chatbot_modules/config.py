"""
Configuration settings for the Agentic RAG system
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    # Ingestion Agent
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    
    # Retrieval Agent
    default_search_k: int = 5
    similarity_threshold: float = 0.7
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # LLM Agent
    model_name: str = "gemini-2.0-flash"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Vector Store
    collection_name: str = "document_store"
    persist_directory: str = "./chroma_db"

@dataclass
class SystemConfig:
    """System-wide configuration"""
    # File handling
    max_file_size_mb: int = 32
    allowed_extensions: set = None
    upload_folder: str = "uploads"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = True
    
    # Security
    secret_key: str = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {"pdf", "docx", "pptx", "csv", "txt", "md"}
        
        if self.secret_key is None:
            self.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.agent = AgentConfig()
        self.system = SystemConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Agent config
        self.agent.chunk_size = int(os.getenv("CHUNK_SIZE", self.agent.chunk_size))
        self.agent.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", self.agent.chunk_overlap))
        self.agent.default_search_k = int(os.getenv("DEFAULT_SEARCH_K", self.agent.default_search_k))
        self.agent.embedding_model = os.getenv("EMBEDDING_MODEL", self.agent.embedding_model)
        self.agent.model_name = os.getenv("LLM_MODEL", self.agent.model_name)
        
        # System config
        self.system.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", self.system.max_file_size_mb))
        self.system.upload_folder = os.getenv("UPLOAD_FOLDER", self.system.upload_folder)
        self.system.log_level = os.getenv("LOG_LEVEL", self.system.log_level)
        self.system.api_host = os.getenv("API_HOST", self.system.api_host)
        self.system.api_port = int(os.getenv("API_PORT", self.system.api_port))
        self.system.debug_mode = os.getenv("DEBUG", "true").lower() == "true"
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask-specific configuration"""
        return {
            "UPLOAD_FOLDER": self.system.upload_folder,
            "MAX_CONTENT_LENGTH": self.system.max_file_size_mb * 1024 * 1024,
            "SECRET_KEY": self.system.secret_key,
            "DEBUG": self.system.debug_mode
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": getattr(__import__("logging"), self.system.log_level),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": [
                {"type": "file", "filename": self.system.log_file},
                {"type": "stream"}
            ]
        }

# Global configuration instance
config = Config()