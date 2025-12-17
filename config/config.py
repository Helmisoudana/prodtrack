from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "allow" 

settings = Settings()
