# src/db/repositories.py
"""
Database repositories for G7Static.
Implements clean, reusable database access patterns.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from src.models.models import User, File
from typing import Optional, Dict, Any, List
import uuid

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, password: str, created_by: str = "system") -> User:
        """
        Create a new user.
        The password argument should be the HASHED password.
        """
        user = User(
            username=username,
            hashed_password=password, # Use the provided password hash directly
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(user)
        self.db.flush()  # Get the ID without committing
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.db.scalar(
            select(User).where(
                and_(
                    User.username == username,
                    User.status == 'active'
                )
            )
        )

class FileRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_file(self, user_id: int, file_data: Dict[str, Any], created_by: str) -> File:
        """Create a new file record."""
        file = File(
            user_id=user_id,
            file_id=str(uuid.uuid4()),
            original_filename=file_data['original_filename'],
            stored_filename=file_data['stored_filename'],
            md5_hash=file_data['md5_hash'],
            s3_key=file_data['s3_key'],
            file_size=file_data['file_size'],
            mime_type=file_data['mime_type'],
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(file)
        self.db.flush()  # Get the ID without committing
        return file

    def get_file_by_hash(self, user_id: int, md5_hash: str) -> Optional[File]:
        """Get a file by MD5 hash and user ID."""
        return self.db.scalar(
            select(File).where(
                and_(
                    File.user_id == user_id,
                    File.md5_hash == md5_hash,
                    File.status == 'active'
                )
            )
        )
        
    def get_file_by_file_id(self, user_id: int, file_id: str) -> Optional[File]:
        """Get a file by its public file_id and user ID."""
        return self.db.scalar(
            select(File).where(
                and_(
                    File.user_id == user_id,
                    File.file_id == file_id,
                    File.status == 'active'
                )
            )
        )

    def delete_file(self, file_to_delete: File) -> None:
        """Schedules a File object for deletion from the database."""
        self.db.delete(file_to_delete)

    def get_files_by_user_id(self, user_id: int) -> List[File]:
        """Get all files for a user."""
        return self.db.scalars(
            select(File).where(
                and_(
                    File.user_id == user_id,
                    File.status == 'active'
                )
            ).order_by(File.created_at.desc())
        ).all()