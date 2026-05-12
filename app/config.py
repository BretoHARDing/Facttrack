from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

    ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://facttrack:facttrack@localhost:5432/facttrack"
    JWT_SECRET: str = "dev-secret-change-in-prod-32chars-min!!"
    JWT_REFRESH_SECRET: str = "dev-refresh-secret-32chars-min!!"

    # CAS settings (now properly defined)
    CAS_BACKEND: str = "local"
    CAS_LOCAL_DIR: str = "./cas_store"
    CAS_S3_BUCKET: str = ""
    CAS_S3_PREFIX: str = "cas/"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # LLM Settings
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemini-2.5-flash"

settings = Settings()
