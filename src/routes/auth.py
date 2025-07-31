# src/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from src.log import logger
from src.schemas import UserCreate, Token, ErrorResponse
from src.config import Config
from src.db.database import get_db
from src.db.repositories import UserRepository
from src.utils.security import create_access_token, get_password_hash, verify_password

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Username already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Token:
    """
    Register a new user and return a JWT access token.
    """
    user_repo = UserRepository(db)
    
    if user_repo.get_user_by_username(user_in.username):
        logger.warning(f"Registration failed for existing username: {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
        
    try:
        hashed_password = get_password_hash(user_in.password)
        user = user_repo.create_user(
            username=user_in.username, 
            password=hashed_password,
            created_by=user_in.username
        )
        db.commit()
        logger.info(f"User '{user.username}' created successfully.")

        access_token_expires = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except IntegrityError:
        db.rollback()
        logger.error(f"Database integrity error during registration for {user_in.username}.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    except HTTPException:
        raise # Re-raise HTTPException directly
    except Exception as e:
        db.rollback()
        logger.error(f"Error during user registration for {user_in.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        )

@auth_router.post(
    "/login", 
    response_model=Token,
    responses={
        401: {"model": ErrorResponse, "description": "Incorrect username or password"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """ 
    Log in a user and return a JWT access token.
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_username(form_data.username)

        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.info(f"User '{user.username}' logged in successfully.")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise # Re-raise HTTPException directly to return 401, not 500
    except Exception as e:
        logger.error(f"Error during login for {form_data.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login.",
        )