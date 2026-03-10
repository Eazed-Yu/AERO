from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DATABASE: str = "aero"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )

    # LLM Provider: "ollama" or "api"
    LLM_PROVIDER: str = "ollama"

    # Ollama (local)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3:latest"
    OLLAMA_EMBEDDING_DIM: int = 1024

    # API (SiliconFlow / OpenAI compatible)
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.siliconflow.cn/v1"
    LLM_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024

    # LightRAG Server (可选)
    ENABLE_LIGHTRAG_SERVER: bool = False  # 是否启动 LightRAG Web UI 服务器
    LIGHTRAG_SERVER_PORT: int = 8030
    LIGHTRAG_SERVER_HOST: str = "127.0.0.1"

    # LightRAG 配置
    LIGHTRAG_LLM_BINDING: str = "openai"  # openai, ollama, azure_openai, gemini
    LIGHTRAG_LLM_HOST: str = ""  # 留空使用默认，或自定义如 http://localhost:11434
    LIGHTRAG_LLM_MODEL: str = "qwen-plus"
    LIGHTRAG_EMBEDDING_BINDING: str = "openai"  # openai, ollama
    LIGHTRAG_EMBEDDING_HOST: str = ""
    LIGHTRAG_EMBEDDING_MODEL: str = "text-embedding-v3"
    LIGHTRAG_EMBEDDING_DIM: int = 1024

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
