"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Nutrient Recommendation System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017/nutrient_db"
    DATABASE_NAME: str = "nutrient_db"
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # External APIs
    GEMINI_API_KEY: str = ""
    USDA_API_KEY: str = ""
    
    # ML Configuration
    MODEL_PATH: str = "./ml-models"
    ENABLE_MODEL_TRAINING: bool = True
    
    # Features
    ENABLE_IMAGE_PROCESSING: bool = True
    ENABLE_GEMINI_PARSING: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
