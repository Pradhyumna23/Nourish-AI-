"""
Authentication endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

from app.models.user import User, UserCreate, UserResponse
from app.core.config import settings
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await User.find_one(
            {"$or": [{"email": user_data.email}, {"username": user_data.username}]}
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create new user
        user_service = UserService()
        user = await user_service.create_user(user_data)
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            age=user.age,
            gender=user.gender,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            activity_level=user.activity_level,
            primary_goal=user.primary_goal,
            target_weight_kg=user.target_weight_kg,
            target_calories=user.target_calories,
            health_conditions=user.health_conditions,
            dietary_restrictions=user.dietary_restrictions,
            allergies=user.allergies,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    try:
        auth_service = AuthService()
        
        # Authenticate user
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save()
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                age=user.age,
                gender=user.gender,
                height_cm=user.height_cm,
                weight_kg=user.weight_kg,
                activity_level=user.activity_level,
                primary_goal=user.primary_goal,
                target_weight_kg=user.target_weight_kg,
                target_calories=user.target_calories,
                health_conditions=user.health_conditions,
                dietary_restrictions=user.dietary_restrictions,
                allergies=user.allergies,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(AuthService.get_current_user)):
    """Refresh access token."""
    try:
        auth_service = AuthService()
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": current_user.username}, expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(current_user.id),
                username=current_user.username,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                age=current_user.age,
                gender=current_user.gender,
                height_cm=current_user.height_cm,
                weight_kg=current_user.weight_kg,
                activity_level=current_user.activity_level,
                primary_goal=current_user.primary_goal,
                target_weight_kg=current_user.target_weight_kg,
                target_calories=current_user.target_calories,
                health_conditions=current_user.health_conditions,
                dietary_restrictions=current_user.dietary_restrictions,
                allergies=current_user.allergies,
                is_active=current_user.is_active,
                is_verified=current_user.is_verified,
                created_at=current_user.created_at
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(AuthService.get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        age=current_user.age,
        gender=current_user.gender,
        height_cm=current_user.height_cm,
        weight_kg=current_user.weight_kg,
        activity_level=current_user.activity_level,
        primary_goal=current_user.primary_goal,
        target_weight_kg=current_user.target_weight_kg,
        target_calories=current_user.target_calories,
        health_conditions=current_user.health_conditions,
        dietary_restrictions=current_user.dietary_restrictions,
        allergies=current_user.allergies,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )
