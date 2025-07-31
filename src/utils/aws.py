# src/utils/aws.py
"""
Utility module for AWS S3 client initialization and dependency injection.
"""
import boto3
from src.config import Config
from src.log import logger
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# --- Client Initialization ---
# This block runs only once when the application starts, creating a single, shared client.
try:
    logger.info("Initializing shared AWS S3 client...")
    s3_config = BotoConfig(
        s3={'addressing_style': 'path'}
    )
    # This s3_client instance will be reused across the application
    s3_client = boto3.client(
        's3',
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION,
        config=s3_config
    )
    logger.info("Shared AWS S3 client initialized successfully.")
except (NoCredentialsError, PartialCredentialsError) as e:
    logger.critical(f"AWS credentials not found or incomplete: {e}. Please check your .env file.")
    raise
except Exception as e:
    logger.critical(f"An unexpected error occurred during AWS S3 client initialization: {e}")
    raise

# --- FastAPI Dependency ---
def get_s3_client():
    """
    FastAPI dependency that provides the shared S3 client instance.
    """
    return s3_client