"""
Real MongoDB database setup and connection.
Replace in-memory storage with persistent MongoDB storage.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Dict, List, Any, Optional

class DatabaseService:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nutrient_db")
        self.database_name = "nutrient_recommendation_db"
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB database."""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB successfully!")
            
            # Create indexes for better performance
            await self.create_indexes()
            
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def create_indexes(self):
        """Create database indexes for better performance."""
        
        # Users collection indexes
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index("email", unique=True)
        
        # Food logs collection indexes
        await self.db.food_logs.create_index([("user_id", 1), ("date", -1)])
        await self.db.food_logs.create_index("fdc_id")
        
        # Recommendations collection indexes
        await self.db.recommendations.create_index([("user_id", 1), ("created_at", -1)])
        await self.db.recommendations.create_index("is_active")
        
        print("📊 Database indexes created successfully!")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("🔌 Disconnected from MongoDB")
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in the database."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.users.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        
        return user_data
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        user = await self.db.users.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        user = await self.db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user information."""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    # Food logging operations
    async def log_food(self, food_log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a food entry."""
        food_log_data["created_at"] = datetime.utcnow()
        
        result = await self.db.food_logs.insert_one(food_log_data)
        food_log_data["_id"] = str(result.inserted_id)
        
        return food_log_data
    
    async def get_daily_food_logs(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get all food logs for a specific date."""
        logs = await self.db.food_logs.find({
            "user_id": user_id,
            "date": {"$regex": f"^{date}"}
        }).to_list(length=None)
        
        for log in logs:
            log["_id"] = str(log["_id"])
        
        return logs
    
    async def get_food_history(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get food history for the last N days."""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = await self.db.food_logs.find({
            "user_id": user_id,
            "created_at": {"$gte": start_date}
        }).sort("created_at", -1).to_list(length=100)
        
        for log in logs:
            log["_id"] = str(log["_id"])
        
        return logs
    
    # Recommendations operations
    async def save_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a recommendation."""
        recommendation_data["created_at"] = datetime.utcnow()
        recommendation_data["is_active"] = True
        
        result = await self.db.recommendations.insert_one(recommendation_data)
        recommendation_data["_id"] = str(result.inserted_id)
        
        return recommendation_data
    
    async def get_user_recommendations(self, user_id: str, active_only: bool = True, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recommendations for a user."""
        query = {"user_id": user_id}
        if active_only:
            query["is_active"] = True
        
        recommendations = await self.db.recommendations.find(query).sort("created_at", -1).limit(limit).to_list(length=None)
        
        for rec in recommendations:
            rec["_id"] = str(rec["_id"])
        
        return recommendations
    
    async def update_recommendation_feedback(self, recommendation_id: str, feedback_data: Dict[str, Any]) -> bool:
        """Update recommendation with user feedback."""
        feedback_data["feedback_at"] = datetime.utcnow()
        
        result = await self.db.recommendations.update_one(
            {"_id": recommendation_id},
            {"$set": feedback_data}
        )
        
        return result.modified_count > 0

# Database connection instance
db_service = DatabaseService()

async def test_database_connection():
    """Test the database connection and operations."""
    
    print("🔌 Testing MongoDB connection...")
    
    if await db_service.connect():
        print("✅ Database connection successful!")
        
        # Test user creation
        test_user = {
            "username": "test_user",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password"
        }
        
        try:
            created_user = await db_service.create_user(test_user)
            print(f"✅ Test user created: {created_user['username']}")
            
            # Test user retrieval
            retrieved_user = await db_service.get_user_by_username("test_user")
            print(f"✅ User retrieved: {retrieved_user['email']}")
            
            # Test food logging
            food_log = {
                "user_id": created_user["_id"],
                "fdc_id": 123456,
                "food_description": "Test Food",
                "quantity": 1.0,
                "unit": "serving",
                "meal_type": "lunch",
                "date": "2024-01-15",
                "calories": 200,
                "protein_g": 10,
                "carbs_g": 30,
                "fat_g": 5
            }
            
            logged_food = await db_service.log_food(food_log)
            print(f"✅ Food logged: {logged_food['food_description']}")
            
            # Test recommendation saving
            recommendation = {
                "user_id": created_user["_id"],
                "recommendation_type": "NUTRIENT_ADJUSTMENT",
                "title": "Test Recommendation",
                "description": "This is a test recommendation",
                "confidence_level": "high",
                "priority": 2
            }
            
            saved_rec = await db_service.save_recommendation(recommendation)
            print(f"✅ Recommendation saved: {saved_rec['title']}")
            
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
        
        await db_service.disconnect()
    else:
        print("❌ Database connection failed!")

if __name__ == "__main__":
    asyncio.run(test_database_connection())
