# src/routes/upload.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib
import mimetypes
import os
import secrets
import boto3

from src.config import Config
from src.db.database import get_db
from src.db.repositories import FileRepository
from src.log import logger
from src.models.models import User
from src.schemas import ErrorResponse, FileResponse
from src.utils.security import get_current_user
from src.utils.aws import get_s3_client  # Import the dependency
from botocore.exceptions import BotoCoreError, ClientError

upload_router = APIRouter(prefix="/upload", tags=["Upload"])

@upload_router.post(
    '/audio',
    status_code=status.HTTP_201_CREATED,
    response_model=FileResponse,
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        409: {"model": ErrorResponse, "description": "Duplicate file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def upload_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    s3_client: boto3.client = Depends(get_s3_client)  # Use the shared client
):
    max_file_size = Config.MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024
    username = current_user.username

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    # Validate file type
    allowed_exts = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not file.filename.lower().endswith(allowed_exts) or not mime_type or not mime_type.startswith('audio/'):
        logger.warning(f"User '{username}' tried to upload unsupported file type: {file.filename}")
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported audio file type.")

    try:
        # --- PERFORMANCE IMPROVEMENT: STREAMING HASH & SIZE CALCULATION ---
        # This avoids loading the entire file into memory.
        md5 = hashlib.md5()
        file_size = 0
        await file.seek(0)
        while chunk := await file.read(8192):  # Read in 8KB chunks
            md5.update(chunk)
            file_size += len(chunk)
        
        if file_size > max_file_size:
            logger.warning(f"User '{username}' file too large: {file_size} bytes")
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File size exceeds {Config.MAX_UPLOAD_FILE_SIZE_MB}MB.")
        
        md5_hash = md5.hexdigest()
        # --- END OF PERFORMANCE IMPROVEMENT ---

        file_repo = FileRepository(db)
        if existing := file_repo.get_file_by_hash(current_user.id, md5_hash):
            logger.info(f"User '{username}' tried to upload duplicate file (hash: {md5_hash}).")
            return FileResponse(message="File already uploaded", filename=existing.original_filename, md5_hash=md5_hash, s3_key=existing.s3_key)

        stored_filename = file.filename
        s3_key = f"{Config.AUDIO_KEY}/{username}/{stored_filename}"

        # Check if a file with this name already exists in S3 and rename if necessary
        try:
            s3_client.head_object(Bucket=Config.AWS_S3_BUCKET_NAME, Key=s3_key)
            name, ext = os.path.splitext(file.filename)
            stored_filename = f"{name}_{secrets.token_hex(4)}{ext}"
            s3_key = f"{Config.AUDIO_KEY}/{username}/{stored_filename}"
        except ClientError as e:
            if e.response['Error']['Code'] != '404': # 404 is expected (file not found)
                logger.error(f"Error checking S3 for file '{s3_key}': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error checking file existence in storage.")

        # Rewind the file pointer before uploading
        await file.seek(0)
        
        # Upload the file to S3
        s3_client.upload_fileobj(file.file, Config.AWS_S3_BUCKET_NAME, s3_key)
        
        # Save file metadata to the database
        file_data = {
            'original_filename': file.filename, 'stored_filename': stored_filename,
            'md5_hash': md5_hash, 's3_key': s3_key, 'file_size': file_size, 
            'mime_type': mime_type or 'application/octet-stream'
        }
        file_repo.create_file(current_user.id, file_data, created_by=username)
        db.commit()
        
        logger.info(f"Audio file uploaded to S3 for user '{username}': {s3_key}")
        return FileResponse(message="Audio file uploaded successfully", filename=stored_filename, md5_hash=md5_hash, s3_key=s3_key)

    except (BotoCoreError, ClientError) as e:
        db.rollback()
        logger.error(f"S3 upload error for user '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not upload file to storage service.")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error uploading audio for user '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")