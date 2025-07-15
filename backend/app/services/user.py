"""
User service for user management operations.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
from loguru import logger

from app.models.user import User, UserCreate, UserUpdate, HealthCondition, DietaryRestriction
from app.services.auth import AuthService


class UserService:
    """User service class."""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Hash the password
            password_hash = self.auth_service.get_password_hash(user_data.password)
            
            # Create user document
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            await user.insert()
            logger.info(f"User created successfully: {user.username}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            user = await User.get(user_id)
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            user = await User.find_one({"username": username})
            return user
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            user = await User.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            # Update fields that are provided
            update_data = user_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"User updated successfully: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
    
    async def add_health_condition(self, user_id: str, condition: HealthCondition) -> Optional[User]:
        """Add health condition to user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            # Check if condition already exists
            for existing_condition in user.health_conditions:
                if existing_condition.name.lower() == condition.name.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Health condition already exists"
                    )
            
            user.health_conditions.append(condition)
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"Health condition added to user {user.username}: {condition.name}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add health condition to user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add health condition: {str(e)}"
            )
    
    async def remove_health_condition(self, user_id: str, condition_name: str) -> Optional[User]:
        """Remove health condition from user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            # Find and remove condition
            user.health_conditions = [
                condition for condition in user.health_conditions
                if condition.name.lower() != condition_name.lower()
            ]
            
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"Health condition removed from user {user.username}: {condition_name}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to remove health condition from user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove health condition: {str(e)}"
            )
    
    async def add_dietary_restriction(self, user_id: str, restriction: DietaryRestriction) -> Optional[User]:
        """Add dietary restriction to user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            # Check if restriction already exists
            for existing_restriction in user.dietary_restrictions:
                if existing_restriction.type.lower() == restriction.type.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Dietary restriction already exists"
                    )
            
            user.dietary_restrictions.append(restriction)
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"Dietary restriction added to user {user.username}: {restriction.type}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add dietary restriction to user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add dietary restriction: {str(e)}"
            )
    
    async def remove_dietary_restriction(self, user_id: str, restriction_type: str) -> Optional[User]:
        """Remove dietary restriction from user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            # Find and remove restriction
            user.dietary_restrictions = [
                restriction for restriction in user.dietary_restrictions
                if restriction.type.lower() != restriction_type.lower()
            ]
            
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"Dietary restriction removed from user {user.username}: {restriction_type}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to remove dietary restriction from user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove dietary restriction: {str(e)}"
            )
    
    async def add_allergy(self, user_id: str, allergy: str) -> Optional[User]:
        """Add allergy to user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            if allergy.lower() not in [a.lower() for a in user.allergies]:
                user.allergies.append(allergy)
                user.updated_at = datetime.utcnow()
                await user.save()
                
                logger.info(f"Allergy added to user {user.username}: {allergy}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to add allergy to user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add allergy: {str(e)}"
            )
    
    async def remove_allergy(self, user_id: str, allergy: str) -> Optional[User]:
        """Remove allergy from user."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            user.allergies = [a for a in user.allergies if a.lower() != allergy.lower()]
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"Allergy removed from user {user.username}: {allergy}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to remove allergy from user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove allergy: {str(e)}"
            )
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate user account."""
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            await user.save()
            
            logger.info(f"User deactivated: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate user: {str(e)}"
            )
