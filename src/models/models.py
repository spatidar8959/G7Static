# src/models/models.py
"""
SQLAlchemy models for G7Static.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.database import Base # Base is imported from database.py
from datetime import datetime
from typing import Optional

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=False)

    # Relationships
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")

    # Indices
    __table_args__ = (
        Index('idx_username_status', 'username', 'status'),
    )

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(String(36), unique=True, nullable=False)  # UUID
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    md5_hash = Column(String(32), nullable=False, index=True)
    s3_key = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(128), nullable=False)
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=False)

    # Relationships
    user = relationship("User", back_populates="files")

    # Indices
    __table_args__ = (
        Index('idx_user_id_status', 'user_id', 'status'),
        Index('idx_md5_hash_user_id', 'md5_hash', 'user_id'),
        Index('idx_created_at', 'created_at'),
    )