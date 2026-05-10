from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os

class Settings(BaseSettings):
    llm_provider: str = "ollama"
    gemini_api_key: str = "[ENCRYPTION_KEY]" #add your key here
    gemini_model: str = "gemini-2.0-flash"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    chroma_persist_dir: str = "./chroma_db"
    log_level: str = "INFO"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def load_agent_config(self) -> dict:
        config_path = os.path.join(os.path.dirname(__file__), "agents.yaml")
        with open(config_path) as f:
            return yaml.safe_load(f)

settings = Settings()
