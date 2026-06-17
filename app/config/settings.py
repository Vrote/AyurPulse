from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AyurPulse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Model
    MODEL_PATH: str = "saved_models/face_skin_disease_model.pth"
    NUM_CLASSES: int = 5

    # Thresholds
    DISEASE_THRESHOLD: float = 88.0
    WRINKLE_THRESHOLD: float = 96.0

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ayurpulse_db"

    # Upload
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5

    # JWT Auth
    ACCESS_TOKEN_SECRET: str = "change-this-access-secret-in-production"
    REFRESH_TOKEN_SECRET: str = "change-this-refresh-secret-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Groq API Key
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()