"""
Database configuration and connection management.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from app.core.config import settings
from app.models.user import User
from app.models.food import Food, FoodItem
from app.models.nutrition import NutritionProfile, DailyIntake
from app.models.recommendation import Recommendation


class Database:
    """Database connection manager."""
    
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def get_database():
    """Get database instance."""
    return db.database


async def init_database():
    """Initialize database connection and models."""
    try:
        # Create MongoDB client
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Initialize Beanie with document models
        await init_beanie(
            database=db.database,
            document_models=[
                User,
                Food,
                FoodItem,
                NutritionProfile,
                DailyIntake,
                Recommendation
            ]
        )
        
        logger.info("Database models initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_database():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Database connection closed")
