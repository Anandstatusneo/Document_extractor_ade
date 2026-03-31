"""
Backend configuration settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document AI API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:8501",
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    UPLOAD_DIR: str = "uploads"
    
    # OCR Configuration
    DEFAULT_OCR_ENGINE: str = "tesseract"  # tesseract, mistral, landingai, docling
    
    # LandingAI Configuration
    VISION_AGENT_API_KEY: Optional[str] = None
    
    # Hugging Face Configuration
    HF_TOKEN: Optional[str] = None
    
    # Groq Configuration
    GROQ_API_KEY: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None

    # Mistral Configuration
    MISTRAL_API_KEY: Optional[str] = None
    
    # Database Configuration (for future use)
    DATABASE_URL: Optional[str] = None
    
    # Redis Configuration (for caching)
    REDIS_URL: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env


# Global settings instance
settings = Settings()
