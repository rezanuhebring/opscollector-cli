from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./server_sync.db"
    SECRET_KEY: str = "change-me-local-dev"
    TOKEN_ROTATION_DAYS: int = 30
    TOKEN_LENGTH: int = 32
    SERVER_SCHEMA_VERSION: int = 1
    ALLOWED_DRIFT: int = 0

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
