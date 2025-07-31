# run.py
import uvicorn
from src.app import app
from src.config import Config
from src.db.database import init_db
from src.log import logger

if __name__ == '__main__':
    # Validate environment variables
    try:
        Config.validate()
        logger.info("Environment variables validated successfully.")
    except EnvironmentError as e:
        logger.critical(f"Configuration validation failed: {e}")
        exit(1) # Exit if essential environment variables are missing

    # Create MySQL tables if they don't exist
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database tables: {e}")
        exit(1) # Exit if database initialization fails

    # Run the application
    logger.info(f"Starting Uvicorn server on {Config.APP_HOST}:{Config.APP_PORT}")
    uvicorn.run(
        app=app,
        host=Config.APP_HOST,
        port=Config.APP_PORT
    )