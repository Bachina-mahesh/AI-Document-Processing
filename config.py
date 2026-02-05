"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"
    
    # Storage
    upload_dir: str = "./uploads"
    state_dir: str = "./state"
    
    # Processing
    max_concurrent_requests: int = 5
    processing_timeout: int = 300
    confidence_threshold: float = 0.7
    
    # LLM Settings - OLLAMA (Primary)
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    
    # Optional: Google Gemini (Fallback - not required)
    google_api_key: Optional[str] = None
    llm_model: str = "gemini-pro"
    llm_temperature: float = 0.1
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = "ignore"

settings = Settings()