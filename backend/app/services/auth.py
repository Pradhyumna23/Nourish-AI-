"""
Authentication service for user management and JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger

from app.core.config import settings
from app.models.user import User


class AuthService:
    """Authentication service class."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        try:
            # Find user by username or email
            user = await User.find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: User inactive - {username}")
                return None
            
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None
            
            logger.info(f"User authenticated successfully - {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token"))) -> User:
        """Get current user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
        
        user = await User.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    @staticmethod
    async def get_current_active_user(current_user: User = Depends(lambda: AuthService().get_current_user)) -> User:
        """Get current active user (dependency)."""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
