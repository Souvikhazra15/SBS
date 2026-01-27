"""
VerifyAI KYC Platform - FastAPI Backend
Clean startup with minimal logging
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Validate required environment variables
if not os.getenv("DATABASE_URL"):
    logger.error("❌ DATABASE_URL not found in .env file")
    sys.exit(1)

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import aiofiles
import asyncpg

# Global database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_pool
    
    # Startup
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        db_pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        
        # Set the pool for prisma module
        from src.config.prisma import set_db_pool
        set_db_pool(db_pool)
        
        # Test database connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        logger.info("✔ Database connected")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        sys.exit(1)
    
    # Log API registration
    logger.info("✔ APIs registered")
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()

# Import API routers
from src.api.v1.auth import router as auth_router
from src.api.v1.fake_document import router as fake_document_router
from src.api.v1.face_matching import router as face_matching_router
from src.api.v1.deepfake import router as deepfake_router
from src.api.v1.risk_scoring import router as risk_scoring_router
# from src.api.v1.video_kyc import router as video_kyc_router  # TODO: Enable after database migration

# Initialize FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="VerifyAI KYC Platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": request.url.path
        }
    )

# Register API routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(fake_document_router, prefix="/api/v1")
app.include_router(face_matching_router, prefix="/api/v1")
app.include_router(deepfake_router, prefix="/api/v1")
app.include_router(risk_scoring_router, prefix="/api/v1")
# app.include_router(video_kyc_router, prefix="/api/v1")  # TODO: Enable after database migration

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "VerifyAI KYC Platform API",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "healthy"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy",
            "database": db_status,
            "version": "2.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# File upload endpoint
@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "video/mp4", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported"
            )
        
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        new_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / new_filename
        
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "success": True,
            "filename": new_filename,
            "file_path": str(file_path),
            "file_size": len(content)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("✔ Backend started at http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        log_level="error",
        access_log=False
    )
