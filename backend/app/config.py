from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Dict, List

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
    app_api_keys: str = ""
    max_query_history: int = 10000
    query_history_retention_days: int = 30

    def get_api_key_owners(self) -> Dict[str, str]:
        if not self.app_api_keys.strip():
            return {}
        mapping: Dict[str, str] = {}
        for pair in self.app_api_keys.split(","):
            pair = pair.strip()
            if ":" in pair:
                key, owner = pair.split(":", 1)
                mapping[key.strip()] = owner.strip()
        return mapping

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    model_config = {
        "protected_namespaces": ("settings_",),
        "env_file": ".env",
        "populate_by_name": True,
    }

settings = Settings()
