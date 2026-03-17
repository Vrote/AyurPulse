from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str

    ACCESS_TOKEN_SECRET: str
    REFRESH_TOKEN_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()