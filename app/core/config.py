from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Closira Enquiry API"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./closira.db"

    class Config:
        env_file = ".env"


settings = Settings()