"""
User management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from pydantic import BaseModel

from app.models.user import User, UserUpdate, UserResponse, HealthCondition, DietaryRestriction
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()


class HealthConditionRequest(BaseModel):
    name: str
    severity: str = None
    notes: str = None


class DietaryRestrictionRequest(BaseModel):
    type: str
    severity: str = None
    notes: str = None


class AllergyRequest(BaseModel):
    allergy: str


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(AuthService.get_current_active_user)):
    """Get current user's profile."""
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


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Update current user's profile."""
    user_service = UserService()
    
    updated_user = await user_service.update_user(str(current_user.id), user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.post("/health-conditions", response_model=UserResponse)
async def add_health_condition(
    condition_data: HealthConditionRequest,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Add health condition to user profile."""
    user_service = UserService()
    
    condition = HealthCondition(
        name=condition_data.name,
        severity=condition_data.severity,
        notes=condition_data.notes
    )
    
    updated_user = await user_service.add_health_condition(str(current_user.id), condition)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.delete("/health-conditions/{condition_name}", response_model=UserResponse)
async def remove_health_condition(
    condition_name: str,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Remove health condition from user profile."""
    user_service = UserService()
    
    updated_user = await user_service.remove_health_condition(str(current_user.id), condition_name)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.post("/dietary-restrictions", response_model=UserResponse)
async def add_dietary_restriction(
    restriction_data: DietaryRestrictionRequest,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Add dietary restriction to user profile."""
    user_service = UserService()
    
    restriction = DietaryRestriction(
        type=restriction_data.type,
        severity=restriction_data.severity,
        notes=restriction_data.notes
    )
    
    updated_user = await user_service.add_dietary_restriction(str(current_user.id), restriction)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.delete("/dietary-restrictions/{restriction_type}", response_model=UserResponse)
async def remove_dietary_restriction(
    restriction_type: str,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Remove dietary restriction from user profile."""
    user_service = UserService()
    
    updated_user = await user_service.remove_dietary_restriction(str(current_user.id), restriction_type)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.post("/allergies", response_model=UserResponse)
async def add_allergy(
    allergy_data: AllergyRequest,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Add allergy to user profile."""
    user_service = UserService()
    
    updated_user = await user_service.add_allergy(str(current_user.id), allergy_data.allergy)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.delete("/allergies/{allergy}", response_model=UserResponse)
async def remove_allergy(
    allergy: str,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Remove allergy from user profile."""
    user_service = UserService()
    
    updated_user = await user_service.remove_allergy(str(current_user.id), allergy)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        gender=updated_user.gender,
        height_cm=updated_user.height_cm,
        weight_kg=updated_user.weight_kg,
        activity_level=updated_user.activity_level,
        primary_goal=updated_user.primary_goal,
        target_weight_kg=updated_user.target_weight_kg,
        target_calories=updated_user.target_calories,
        health_conditions=updated_user.health_conditions,
        dietary_restrictions=updated_user.dietary_restrictions,
        allergies=updated_user.allergies,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


@router.delete("/profile", response_model=dict)
async def deactivate_account(
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Deactivate user account."""
    user_service = UserService()
    
    updated_user = await user_service.deactivate_user(str(current_user.id))
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Account deactivated successfully"}
