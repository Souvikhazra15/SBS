"""
Authentication API Routes

RESTful endpoints for user registration, login, and token management.
Handles JWT authentication with secure password hashing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from src.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, RefreshTokenRequest
from src.utils.auth import AuthService, get_current_active_user, create_user_tokens
from src.config.prisma import prisma

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    """
    Register a new user account.
    
    - **email**: Valid email address (will be used as username)
    - **password**: Strong password (min 8 characters)
    - **firstName**: Optional first name
    - **lastName**: Optional last name
    - **phone**: Optional phone number
    
    Returns JWT tokens for immediate authentication after registration.
    """
    try:
        # Check if user already exists
        existing_user = await prisma.user.find_unique(
            where={"email": user_data.email}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )
        
        # Hash password
        password_hash = AuthService.hash_password(user_data.password)
        
        # Create user
        new_user = await prisma.user.create({
            "email": user_data.email,
            "passwordHash": password_hash,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "phone": user_data.phone,
            "role": "USER",
            "status": "ACTIVE"  # Auto-activate for demo purposes
        })
        
        # Create tokens
        tokens = create_user_tokens({
            "id": new_user["id"],
            "email": new_user["email"],
            "role": new_user["role"],
            "status": new_user["status"]
        })
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token and refresh token for API authentication.
    """
    try:
        # Find user by email
        user = await prisma.user.find_unique(
            where={"email": login_data.email}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not AuthService.verify_password(login_data.password, user["passwordHash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if user["status"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user['status'].lower()}. Please contact support."
            )
        
        # Create tokens
        tokens = create_user_tokens({
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"]
        })
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and optionally a new refresh token.
    """
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_data.refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # Fetch user to ensure they still exist and are active
        user = await prisma.user.find_unique(
            where={"id": user_id}
        )
        
        if not user or user["status"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive"
            )
        
        # Create new tokens
        tokens = create_user_tokens({
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"]
        })
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_active_user)):
    """
    Get current user's profile information.
    
    Requires valid JWT token in Authorization header.
    Returns user profile data excluding sensitive information.
    """
    try:
        # Fetch full user data from database
        user = await prisma.user.find_unique(
            where={"id": current_user["id"]}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            firstName=user.get("firstName"),
            lastName=user.get("lastName"),
            phone=user.get("phone"),
            role=user["role"],
            status=user["status"],
            createdAt=user["createdAt"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}"
        )

@router.post("/logout")
async def logout_user(current_user: dict = Depends(get_current_active_user)):
    """
    Logout current user (token invalidation).
    
    In a production system, this would invalidate the current token.
    For this implementation, client should discard the token.
    """
    # In production, you would add the token to a blacklist
    # For now, we'll just return a success message
    return {
        "message": "Logged out successfully",
        "user_id": current_user["id"],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user's password.
    
    - **old_password**: Current password for verification
    - **new_password**: New password (min 8 characters)
    
    Requires authentication and current password verification.
    """
    try:
        # Fetch user with password hash
        user = await prisma.user.find_unique(
            where={"id": current_user["id"]}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not AuthService.verify_password(old_password, user["passwordHash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Hash new password
        new_password_hash = AuthService.hash_password(new_password)
        
        # Update password in database
        await prisma.user.update(
            where={"id": user["id"]},
            data={"passwordHash": new_password_hash}
        )
        
        return {
            "message": "Password changed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.get("/validate-token")
async def validate_token(current_user: dict = Depends(get_current_active_user)):
    """
    Validate current JWT token.
    
    Returns token validity and user information.
    Useful for frontend token validation.
    """
    return {
        "valid": True,
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "role": current_user["role"],
            "status": current_user["status"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for authentication service monitoring.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }