# G7Static - Secure Audio Management & Transcription API

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-05998b)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

G7Static is a robust and secure backend service designed for authenticated audio file management, coupled with a fully asynchronous, event-driven transcription pipeline using AWS services. It provides a complete solution for uploading, storing, listing, downloading, and deleting audio files and their corresponding transcripts.

## ✅ Key Features

-   **Secure Authentication:** JWT-based registration and login system for user management.
-   **Authenticated File Management:** Secure endpoints for uploading, listing, downloading, and deleting files.
-   **Cloud Storage Integration:** Uses AWS S3 for scalable and durable storage of audio files and transcripts.
-   **Automated Transcription Pipeline:**
    -   S3 events automatically trigger an AWS Lambda function upon audio upload.
    -   The Lambda function initiates an AWS Transcribe job.
    -   The completed transcript is automatically saved back to S3.
-   **Database Integration:** MySQL database with SQLAlchemy ORM for persisting user and file metadata.
-   **Performance Optimized:**
    -   Streaming-based file uploads to handle large files with low memory usage.
    -   Duplicate upload prevention using MD5 content hashing.
-   **Secure Downloads:** Generates temporary, pre-signed URLs for secure access to private S3 files.

## ⚙️ Technology Stack

| Category           | Technology                                                                          |
| ------------------ | ----------------------------------------------------------------------------------- |
| **Backend**        | Python, FastAPI, Uvicorn, SQLAlchemy, Passlib, Python-JOSE                          |
| **Frontend**       | HTML5, CSS3, JavaScript, Tailwind CSS                                               |
| **Database**       | MySQL                                                                               |
| **Cloud Services** | AWS S3, AWS Lambda, AWS Transcribe                                                  |
| **Toolkit**        | `uv` (for environment and package management), Boto3 (AWS SDK), Alembic (for migrations) |

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

-   Python 3.11+
-   [Git](https://git-scm.com/)
-   [uv](https://github.com/astral-sh/uv) (recommended for fast dependency management)
-   A running MySQL server instance.

### 1. Clone the Repository

First, clone the project to your local machine.

```bash
git clone <your-repository-url>
cd G7Static
```

### 2. Set Up the Python Virtual Environment

Create and activate a virtual environment using `uv`.

```bash
# Create the virtual environment
uv venv .venv
```

**Activate the environment:**
-   **On Windows (PowerShell/CMD):**
    ```powershell
    .venv\Scripts\activate
    ```
-   **On macOS / Linux:**
    ```bash
    source .venv/bin/activate
    ```

### 3. Install Dependencies

Use `uv sync` to install all required dependencies from the lock file, ensuring a consistent setup.

```bash
uv sync
```

### 4. Configure Environment Variables

The application requires several environment variables for database and AWS connections.

1.  Create a new file named `.env` in the root directory of the project.
2.  Copy the content of the template below into your new `.env` file.
3.  Replace the placeholder values with your actual credentials and settings.

#### `.env` Template
```ini
# ---------------------------------
# AWS Credentials and Configuration
# ---------------------------------
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET_NAME=
AWS_REGION=

# Application-specific S3 prefixes
AUDIO_KEY=
TRANSCRIPT_KEY=

APP_NAME=
APP_VERSION=
APP_PORT=
APP_HOST=

MAX_UPLOAD_FILE_SIZE_MB=
FRONTEND_ORIGINS=


# ---------------------------------
# MySQL Database Connection
# ---------------------------------
MYSQL_HOST=
MYSQL_PORT=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=
MYSQL_POOL_SIZE=
MYSQL_POOL_RECYCLE=

# ---------------------------------
# JWT and Application Settings
# ---------------------------------
# Generate a strong secret key (e.g., using `openssl rand -hex 32`)
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=
```

Once your `.env` file is created and filled out, the setup is complete.

## ▶️ Running the Application

You need to run both the backend server and the frontend server.

### Running the Backend (FastAPI)

Use `uv` to run the main application file. The server will start on `http://localhost:8000`.

```bash
uv run run.py
```
You should see logs indicating the server has started successfully.

### Running the Frontend

The frontend is a simple static site. You can serve it using Python's built-in HTTP server.

```bash
# Navigate to the frontend directory
# Assuming your HTML/CSS/JS files are in a 'frontend' subfolder
cd frontend

# Serve the files on port 5500
python -m http.server 5500
```

## 🌐 Accessing the Application

With both the backend and frontend servers running, open your web browser and navigate to:

**`http://localhost:5500`**

You should see the G7Static login and registration page, fully ready to interact with your local backend.