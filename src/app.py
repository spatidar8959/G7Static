# src/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.auth import auth_router
from src.routes.upload import upload_router
from src.routes.files import files_router
from src.config import Config
from src.log import logger

app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="G7Static Backend API for user authentication and file uploads."
)

# Configure CORS
# Ensure Config.FRONTEND_ORIGINS is a list of strings
allow_origins_list = Config.FRONTEND_ORIGINS.split(',') if isinstance(Config.FRONTEND_ORIGINS, str) else []
if not allow_origins_list:
    logger.warning("No frontend origins configured in .env. CORS might be restrictive.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(files_router)

@app.get('/')
def greet() -> str:
    """
    Root endpoint to greet the user.
    """
    return "Hello From G7."