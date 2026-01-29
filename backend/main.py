"""
Deep Defenders KYC Platform - FastAPI Backend
Clean startup with minimal logging
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

# Disable oneDNN/MKLDNN for Windows compatibility
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

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
import ssl

# Global database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_pool
    
    # Startup
    try:
        # Configure SSL context for Windows
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connect to database (optional - continue without it)
        database_url = os.getenv("DATABASE_URL")
        db_pool = None
        
        try:
            db_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=60,
                ssl=ssl_context
            )
            
            # Set the pool for prisma module
            from src.config.prisma import set_db_pool
            set_db_pool(db_pool)
            
            # Test database connection
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info("✔ Database connected")
        except Exception as db_error:
            logger.warning(f"⚠ Database unavailable (OCR will still work): {str(db_error)[:50]}...")
            db_pool = None
        
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")
    
    # Log API registration
    logger.info("✔ APIs registered")
    logger.info("✔ Backend started at http://localhost:8000")
    
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
from src.api.v1.ekyc import router as ekyc_router
from src.api.v1.video_kyc import router as video_kyc_router

# Initialize FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Deep Defenders KYC Platform API",
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
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
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
app.include_router(ekyc_router, prefix="/api/v1")
app.include_router(video_kyc_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Deep Defenders KYC Platform API",
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
