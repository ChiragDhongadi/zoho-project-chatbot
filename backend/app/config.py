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
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_GUARDRAIL_MODEL: str = Field(default="llama-3.1-8b-instant")

    # Portkey configurations
    PORTKEY_API_KEY: str = Field(default="")
    PORTKEY_CONFIG_ID: str = Field(default="")
    # Database config
    DATABASE_URL: str =  Field(default="sqlite+aiosqlite:///zoho_chatbot.db")

    # LangSmith Observability
    LANGCHAIN_TRACING_V2: str = Field(default="false")
    LANGCHAIN_API_KEY: str = Field(default="")
    LANGCHAIN_PROJECT: str = Field(default="zoho-projects-chatbot")
    LANGCHAIN_ENDPOINT: str = Field(default="https://api.smith.langchain.com")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    if settings.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    if settings.LANGCHAIN_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT

