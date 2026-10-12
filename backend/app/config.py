import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Finance Agent"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server & Port
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "finance")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'finance')}"
    )
    # SQLite fallback for quick local testing without PostgreSQL
    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true"
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/finance.db")
    
    # Redis & Broker
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage & Rules
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    RULES_PATH: str = os.getenv("RULES_PATH", "./app/rules/finance_rules.json")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./app/ml/category_model.pkl")
    
    # Security
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "super-secret-session-key-agentic-finance-32bytes")
    SESSION_MAX_AGE_SECONDS: int = 86400 * 7 # 7 days
    DEMO_PASSWORD: str = os.getenv("DEMO_PASSWORD", "Demo@1234")
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "") # e.g. http://localhost:11434/v1
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3.2")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
