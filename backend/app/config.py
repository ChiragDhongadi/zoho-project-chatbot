import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):

    # FastAPI config
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    SECRET_KEY: str = Field(default="super-secret-key-change-in-production")

    # zoho oauth 
    ZOHO_CLIENT_ID: str
    ZOHO_CLIENT_SECRET: str
    ZOHO_REDIRECT_URI: str
    ZOHO_PORTAL_ID: str = Field(default="")
    ZOHO_DOMAIN: str = Field(default="zoho.in")

    # llm config
    GROQ_API_KEY: str
    GROQ_MODEL: str = Field(default="llama-3.1-70b-versatile")

    # Database config
    DATABASE_URL: str =  Field(default="sqlite+aiosqlite:///zoho_chatbot.db")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
