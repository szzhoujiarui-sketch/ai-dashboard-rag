from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model_name: str = Field(default="gpt-3.5-turbo", alias="MODEL_NAME")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./chroma_db"
    upload_dir: str = "./uploads"
    max_file_size: str = "10MB"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    app_api_key: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    model_config = {
        "protected_namespaces": ("settings_",),
        "env_file": ".env",
        "populate_by_name": True,
    }

settings = Settings()
