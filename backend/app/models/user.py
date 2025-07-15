"""
User model and schemas.
"""

from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class Goal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    HEALTH_IMPROVEMENT = "health_improvement"


class HealthCondition(BaseModel):
    """Health condition model."""
    name: str
    severity: Optional[str] = None
    diagnosed_date: Optional[datetime] = None
    notes: Optional[str] = None


class DietaryRestriction(BaseModel):
    """Dietary restriction model."""
    type: str  # vegetarian, vegan, gluten_free, dairy_free, etc.
    severity: Optional[str] = None  # strict, moderate, occasional
    notes: Optional[str] = None


class User(Document):
    """User document model."""
    
    # Basic information
    username: str = Field(..., unique=True, min_length=3, max_length=50)
    email: EmailStr = Field(..., unique=True)
    password_hash: str
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    
    # Profile information
    age: Optional[int] = Field(None, ge=13, le=120)
    gender: Optional[Gender] = None
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    activity_level: Optional[ActivityLevel] = None
    
    # Goals and preferences
    primary_goal: Optional[Goal] = None
    target_weight_kg: Optional[float] = Field(None, gt=0, le=500)
    target_calories: Optional[int] = Field(None, gt=0, le=10000)
    
    # Health information
    health_conditions: List[HealthCondition] = []
    dietary_restrictions: List[DietaryRestriction] = []
    allergies: List[str] = []
    medications: List[str] = []
    
    # Account status
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "username",
            "created_at"
        ]


# Pydantic schemas for API
class UserCreate(BaseModel):
    """Schema for user creation."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)


class UserUpdate(BaseModel):
    """Schema for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=13, le=120)
    gender: Optional[Gender] = None
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    activity_level: Optional[ActivityLevel] = None
    primary_goal: Optional[Goal] = None
    target_weight_kg: Optional[float] = Field(None, gt=0, le=500)
    target_calories: Optional[int] = Field(None, gt=0, le=10000)


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    primary_goal: Optional[Goal] = None
    target_weight_kg: Optional[float] = None
    target_calories: Optional[int] = None
    health_conditions: List[HealthCondition] = []
    dietary_restrictions: List[DietaryRestriction] = []
    allergies: List[str] = []
    is_active: bool
    is_verified: bool
    created_at: datetime
