# src/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional
import re
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters, alphanumeric with underscores"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )

    @validator('username')
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
class FileDetail(BaseModel):
    file_id: str
    original_filename: str
    file_size: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TranscriptDetail(BaseModel):
    key: str
    size: int
    last_modified: datetime

class DownloadURLResponse(BaseModel):
    download_url: str

class DeleteResponse(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class FileResponse(BaseModel):
    message: str
    filename: Optional[str]
    md5_hash: str
    s3_key: Optional[str]

class ErrorResponse(BaseModel):
    detail: str