from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Spotify
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/auth/callback"
    spotify_refresh_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/musicdiscovery"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Scheduler
    schedule_hour: int = 9
    schedule_minute: int = 0
    schedule_timezone: str = "Asia/Seoul"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
