# src/config.py
"""
Configuration loader for G7Static.
Loads environment variables for both AWS and MySQL settings.
"""
from dotenv import load_dotenv
import os
from typing import Optional, Union

load_dotenv()

class Config:
    # AWS Credentials and Region
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION")

    # S3 Configuration
    AWS_S3_BUCKET_NAME: Optional[str] = os.getenv("AWS_S3_BUCKET_NAME")
    AUDIO_KEY: str = os.getenv("AUDIO_KEY")
    TRANSCRIPT_KEY: str = os.getenv("TRANSCRIPT_KEY")

    # MySQL Database Settings
    MYSQL_HOST: str = os.getenv("MYSQL_HOST")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT"))
    MYSQL_USER: str = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD") # This should be set in .env
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE")
    MYSQL_POOL_SIZE: int = int(os.getenv("MYSQL_POOL_SIZE"))
    MYSQL_POOL_RECYCLE: int = int(os.getenv("MYSQL_POOL_RECYCLE"))

    # Application Settings
    APP_NAME: str = os.getenv("APP_NAME")
    APP_VERSION: str = os.getenv("APP_VERSION")
    APP_PORT: int = int(os.getenv("APP_PORT"))
    APP_HOST: str = os.getenv("APP_HOST")
    FRONTEND_ORIGINS: Union[str, list[str]] = os.getenv("FRONTEND_ORIGINS")
    MAX_UPLOAD_FILE_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_FILE_SIZE_MB"))

    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))

    @classmethod
    def validate(cls) -> None:
        """Validate required environment variables are set."""
        required_vars = [
            ("AWS_ACCESS_KEY_ID", cls.AWS_ACCESS_KEY_ID),
            ("AWS_SECRET_ACCESS_KEY", cls.AWS_SECRET_ACCESS_KEY),
            ("AWS_REGION", cls.AWS_REGION),
            ("AWS_S3_BUCKET_NAME", cls.AWS_S3_BUCKET_NAME),
            ("MYSQL_HOST", cls.MYSQL_HOST),
            ("MYSQL_PORT", cls.MYSQL_PORT),
            ("MYSQL_USER", cls.MYSQL_USER),
            ("MYSQL_PASSWORD", cls.MYSQL_PASSWORD),
            ("MYSQL_DATABASE", cls.MYSQL_DATABASE),
            ("JWT_SECRET_KEY", cls.JWT_SECRET_KEY)
        ]
        missing = [name for name, value in required_vars if value is None or (isinstance(value, str) and not value.strip())]
        if missing:
            raise EnvironmentError(f"Missing or empty required environment variables: {', '.join(missing)}")
        if cls.JWT_SECRET_KEY == "your_super_secret_key_change_me":
            raise EnvironmentError("Default JWT_SECRET_KEY is insecure. Please set a new one in your environment.")