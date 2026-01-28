"""
Prisma Database Configuration

Database connection and client initialization for the Deep Defenders platform.
Handles PostgreSQL connection with connection pooling and error handling.
"""

import os
import asyncpg
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# This will be set by main.py during startup
_db_pool: Optional[asyncpg.Pool] = None

def set_db_pool(pool: asyncpg.Pool):
    """Set the database pool (called from main.py)"""
    global _db_pool
    _db_pool = pool

def get_db_pool() -> asyncpg.Pool:
    """Get the current database pool"""
    if _db_pool is None:
        raise RuntimeError("Database pool not initialized. Call set_db_pool first.")
    return _db_pool

# Database client wrapper
class DatabaseClient:
    """Database client with Prisma-like interface"""
    
    class UserModel:
        @staticmethod
        async def find_unique(where: Dict[str, Any]):
            """Find a unique user by email"""
            pool = get_db_pool()
            
            async with pool.acquire() as conn:
                if "email" in where:
                    result = await conn.fetchrow(
                        'SELECT * FROM "users" WHERE email = $1',
                        where["email"]
                    )
                    return dict(result) if result else None
                elif "id" in where:
                    result = await conn.fetchrow(
                        'SELECT * FROM "users" WHERE id = $1',
                        where["id"]
                    )
                    return dict(result) if result else None
                return None

        @staticmethod
        async def create(data: Dict[str, Any]):
            """Create a new user"""
            pool = get_db_pool()
            
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO "users" (
                        id, email, "passwordHash", "firstName", "lastName", 
                        phone, role, status, "emailVerified", "phoneVerified",
                        "createdAt", "updatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING *
                """,
                    user_id,
                    data.get("email"),
                    data.get("passwordHash"),
                    data.get("firstName"),
                    data.get("lastName"),
                    data.get("phone"),
                    data.get("role", "USER"),
                    data.get("status", "ACTIVE"),
                    data.get("emailVerified", False),
                    data.get("phoneVerified", False),
                    now,
                    now
                )
                return dict(result) if result else None

        @staticmethod
        async def update(where: Dict[str, Any], data: Dict[str, Any]):
            """Update a user"""
            pool = get_db_pool()
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                # Build dynamic UPDATE query
                set_clauses = []
                params = []
                param_count = 1
                
                for key, value in data.items():
                    if key == "passwordHash":
                        set_clauses.append(f'"passwordHash" = ${param_count}')
                    elif key == "lastLoginAt":
                        set_clauses.append(f'"lastLoginAt" = ${param_count}')
                    else:
                        set_clauses.append(f'"{key}" = ${param_count}')
                    params.append(value)
                    param_count += 1
                
                # Always update updatedAt
                set_clauses.append(f'"updatedAt" = ${param_count}')
                params.append(now)
                param_count += 1
                
                # Add WHERE clause
                if "id" in where:
                    where_clause = f'id = ${param_count}'
                    params.append(where["id"])
                elif "email" in where:
                    where_clause = f'email = ${param_count}'
                    params.append(where["email"])
                else:
                    return None
                
                query = f'''
                    UPDATE "users" 
                    SET {", ".join(set_clauses)}
                    WHERE {where_clause}
                    RETURNING *
                '''
                
                result = await conn.fetchrow(query, *params)
                return dict(result) if result else None

    class SessionModel:
        @staticmethod
        async def create(data: Dict[str, Any]):
            """Create a session"""
            pool = get_db_pool()
            
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO "sessions" (
                        id, "userId", token, "refreshToken", "expiresAt", "createdAt", "updatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                """,
                    session_id,
                    data.get("userId"),
                    data.get("token"),
                    data.get("refreshToken"),
                    data.get("expiresAt"),
                    now,
                    now
                )
                return dict(result) if result else None

    class VerificationSessionModel:
        @staticmethod
        async def create(data: Dict[str, Any]):
            """Create a verification session"""
            pool = get_db_pool()
            
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO "verification_sessions" (
                        id, "userId", "documentPath", "forgeryScore", decision, "createdAt", "updatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                """,
                    session_id,
                    data.get("userId"),
                    data.get("documentPath"),
                    data.get("forgeryScore", 0.0),
                    data.get("decision", "PENDING"),
                    now,
                    now
                )
                return dict(result) if result else None

    class FeatureResultModel:
        @staticmethod
        async def create(data: Dict[str, Any]):
            """Create a feature result"""
            pool = get_db_pool()
            
            result_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                import json
                result = await conn.fetchrow("""
                    INSERT INTO "feature_results" (
                        id, "sessionId", "featureName", score, metadata, "createdAt", "updatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                """,
                    result_id,
                    data.get("sessionId"),
                    data.get("featureName"),
                    data.get("score", 0.0),
                    json.dumps(data.get("metadata", {})),
                    now,
                    now
                )
                return dict(result) if result else None

    def __init__(self):
        self.user = self.UserModel()
        self.session = self.SessionModel()
        self.verificationSession = self.VerificationSessionModel()
        self.featureResult = self.FeatureResultModel()

# Global prisma-like client
prisma = DatabaseClient()
