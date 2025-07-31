# src/db/database.py
"""
Database configuration and session management for G7Static.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from src.config import Config
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
from src.log import logger
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# Create SQLAlchemy base class for declarative models
Base = declarative_base()

# Create SQLAlchemy engine with connection pooling
DATABASE_URL = (
    f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@"
    f"{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=Config.MYSQL_POOL_SIZE,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=Config.MYSQL_POOL_RECYCLE,
    pool_pre_ping=True,  # Enable connection health checks
    echo=False  # Set to True for SQL query logging (useful for debugging)
)

# Create sessionmaker
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session and ensures it's closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database by creating the database if it doesn't exist,
    then creating all tables within it.
    Also attempts to test the database connection.
    """
    logger.info("Attempting to initialize database...")
    try:
        # First, connect to MySQL without specifying a database to create it if it doesn't exist
        temp_engine_url = (
            f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@"
            f"{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/" # Connect without a specific database
        )
        temp_engine = create_engine(temp_engine_url)

        with temp_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}"))
            connection.commit() # Commit the database creation
        logger.info(f"Database '{Config.MYSQL_DATABASE}' ensured to exist.")

        # Now, proceed with the main engine (which connects to the specific database)
        # Test connection by trying to connect
        with engine.connect() as connection:
            connection.scalar(text("SELECT 1")) # Use text() for literal SQL
        logger.info("Successfully connected to the application database.")

        # Import models here to ensure they are registered with Base.metadata
        # This prevents circular imports if models import Base from this file
        from src.models.models import User, File # noqa: F401, E501

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created or already exist.")
    except OperationalError as e:
        logger.error(f"Database connection or creation failed: {e}")
        raise ConnectionRefusedError(f"Could not connect to or create the database. Please check connection details and ensure the MySQL server is running: {e}")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during database initialization: {e}", exc_info=True)
        raise RuntimeError(f"Database initialization failed due to a SQLAlchemy error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during database initialization: {e}", exc_info=True)
        raise RuntimeError(f"An unexpected error occurred during database initialization: {e}")