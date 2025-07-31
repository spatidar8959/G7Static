# src/routes/files.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import boto3

from src.config import Config
from src.db.database import get_db
from src.db.repositories import FileRepository
from src.log import logger
from src.models.models import User
from src.schemas import FileDetail, TranscriptDetail, DownloadURLResponse, DeleteResponse
from src.utils.security import get_current_user
from src.utils.aws import get_s3_client
from botocore.exceptions import ClientError

files_router = APIRouter(prefix="/files", tags=["Files"])

@files_router.get("/audio", response_model=List[FileDetail])
async def list_audio_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_repo = FileRepository(db)
    return file_repo.get_files_by_user_id(current_user.id)

@files_router.get("/transcripts", response_model=List[TranscriptDetail])
async def list_transcription_files(current_user: User = Depends(get_current_user), s3_client: boto3.client = Depends(get_s3_client)):
    prefix = f"StaticTranscription/{current_user.username}/"
    try:
        response = s3_client.list_objects_v2(Bucket=Config.AWS_S3_BUCKET_NAME, Prefix=prefix)
        transcripts = []
        for content in response.get('Contents', []):
            if not content['Key'].endswith('/'):
                transcripts.append({"key": content['Key'], "size": content['Size'], "last_modified": content['LastModified']})
        return transcripts
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Could not list transcripts from S3: {e}")

@files_router.get("/audio/{file_id}/download", response_model=DownloadURLResponse)
async def get_audio_download_url(file_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), s3_client: boto3.client = Depends(get_s3_client)):
    file_repo = FileRepository(db)
    file_record = file_repo.get_file_by_file_id(current_user.id, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    try:
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': Config.AWS_S3_BUCKET_NAME, 'Key': file_record.s3_key}, ExpiresIn=3600)
        return {"download_url": url}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download URL: {e}")

@files_router.get("/transcripts/download", response_model=DownloadURLResponse)
async def get_transcript_download_url(key: str, current_user: User = Depends(get_current_user), s3_client: boto3.client = Depends(get_s3_client)):
    if not key.startswith(f"StaticTranscription/{current_user.username}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    try:
        s3_client.head_object(Bucket=Config.AWS_S3_BUCKET_NAME, Key=key)
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': Config.AWS_S3_BUCKET_NAME, 'Key': key}, ExpiresIn=3600)
        return {"download_url": url}
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
        raise HTTPException(status_code=500, detail=f"Could not generate download URL: {e}")

@files_router.delete("/audio/{file_id}", response_model=DeleteResponse)
async def delete_audio_file(file_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), s3_client: boto3.client = Depends(get_s3_client)):
    file_repo = FileRepository(db)
    file_record = file_repo.get_file_by_file_id(current_user.id, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")

    s3_key = file_record.s3_key
    
    try:
        # Step 1: Delete the database record first.
        file_repo.delete_file(file_record)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting audio record for user '{current_user.username}', file_id '{file_id}': {e}")
        raise HTTPException(status_code=500, detail="Could not delete file record from database.")

    try:
        # Step 2: If DB deletion was successful, delete from S3.
        s3_client.delete_object(Bucket=Config.AWS_S3_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        # CRITICAL: DB record is gone, but S3 file may remain. Log this for manual cleanup.
        logger.critical(f"S3 deletion failed for user '{current_user.username}', key '{s3_key}', after DB record was deleted: {e}")
        # Inform the user of a partial success/failure.
        raise HTTPException(status_code=500, detail="File record deleted, but failed to delete file from storage. Please contact support.")

    logger.info(f"Successfully deleted audio file and record for user '{current_user.username}', s3_key '{s3_key}'.")
    return {"message": "Audio file deleted successfully."}

@files_router.delete("/transcripts", response_model=DeleteResponse)
async def delete_transcript_file(key: str, current_user: User = Depends(get_current_user), s3_client: boto3.client = Depends(get_s3_client)):
    if not key.startswith(f"StaticTranscription/{current_user.username}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        s3_client.delete_object(Bucket=Config.AWS_S3_BUCKET_NAME, Key=key)
    except ClientError as e:
        logger.error(f"S3 deletion failed for user '{current_user.username}', key '{key}': {e}")
        raise HTTPException(status_code=500, detail="Failed to delete transcript file from storage.")

    logger.info(f"Successfully deleted transcript for user '{current_user.username}', s3_key '{key}'.")
    return {"message": "Transcript file deleted successfully."}