from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Social Wishlist API"
    environment: str = "development"

    database_url: str
    sync_database_url: str

    jwt_secret: str
    refresh_secret: str
    viewer_token_pepper: str

    access_token_expires_minutes: int = 15
    refresh_token_expires_days: int = 14

    web_origin: str = "http://localhost:3000"
    api_origin: str = "http://localhost:8000"
    cookie_secure: bool = False

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None


settings = Settings()
