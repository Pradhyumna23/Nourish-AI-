"""
Simple FastAPI application for testing the nutrient recommendation system.
This is a minimal version that doesn't require all dependencies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import json

# Try to import Gemini AI (optional for basic functionality)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    # Configure Gemini if API key is available
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="Nutrient Recommendation System",
    description="AI-powered nutrition recommendations and food tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

class UserLogin(BaseModel):
    username: str
    password: str

class FoodSearch(BaseModel):
    query: str
    page_size: int = 20

class FoodLog(BaseModel):
    food_name: str
    quantity: float
    unit: str
    meal_type: str
    calories: float

# Mock data storage (in production, this would be a database)
users_db = {}
food_logs = []

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Nutrient Recommendation System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/v1/auth/",
            "foods": "/api/v1/foods/",
            "recommendations": "/api/v1/recommendations/"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running successfully"}

# Auth endpoints
@app.post("/api/v1/auth/register")
async def register(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "age": user.age,
        "gender": user.gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "id": len(users_db) + 1
    }
    
    return {
        "message": "User registered successfully",
        "user": users_db[user.username]
    }

@app.post("/api/v1/auth/token")
async def login(credentials: UserLogin):
    if credentials.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # In production, verify password hash
    return {
        "access_token": f"mock_token_{credentials.username}",
        "token_type": "bearer",
        "user": users_db[credentials.username]
    }

@app.get("/api/v1/auth/me")
async def get_current_user():
    # Mock current user - in production, extract from JWT token
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "first_name": "Demo",
        "last_name": "User"
    }

# Food endpoints
@app.get("/api/v1/foods/search")
async def search_foods(query: str, page_size: int = 20):
    # Mock food search results
    mock_foods = [
        {
            "fdc_id": 123456,
            "description": f"Mock {query} - Whole grain bread",
            "brand_owner": "Mock Brand",
            "food_category": "Baked Products",
            "nutrients": {
                "calories": 250,
                "protein_g": 8.5,
                "carbs_g": 45.2,
                "fat_g": 4.1,
                "fiber_g": 6.2
            }
        },
        {
            "fdc_id": 123457,
            "description": f"Mock {query} - Organic variety",
            "brand_owner": "Organic Foods Co",
            "food_category": "Organic Foods",
            "nutrients": {
                "calories": 180,
                "protein_g": 12.0,
                "carbs_g": 25.0,
                "fat_g": 2.5,
                "fiber_g": 8.0
            }
        }
    ]
    
    return {
        "foods": mock_foods,
        "total_hits": len(mock_foods),
        "current_page": 1,
        "total_pages": 1
    }

@app.get("/api/v1/foods/{fdc_id}")
async def get_food_details(fdc_id: int):
    # Mock food details
    return {
        "fdc_id": fdc_id,
        "description": "Mock Food Item",
        "brand_owner": "Mock Brand",
        "food_category": "Mock Category",
        "nutrients": {
            "calories": 200,
            "protein_g": 10.0,
            "carbs_g": 30.0,
            "fat_g": 5.0,
            "fiber_g": 4.0,
            "sugar_g": 8.0,
            "sodium_mg": 150,
            "vitamin_c_mg": 25,
            "calcium_mg": 120,
            "iron_mg": 2.5
        },
        "serving_sizes": [
            {"unit": "cup", "value": 1.0},
            {"unit": "gram", "value": 100.0},
            {"unit": "serving", "value": 1.0}
        ]
    }

@app.post("/api/v1/foods/log")
async def log_food(food_log: FoodLog):
    log_entry = {
        "id": len(food_logs) + 1,
        "food_name": food_log.food_name,
        "quantity": food_log.quantity,
        "unit": food_log.unit,
        "meal_type": food_log.meal_type,
        "calories": food_log.calories,
        "logged_at": "2024-01-15T12:00:00Z"
    }
    food_logs.append(log_entry)
    
    return {
        "message": "Food logged successfully",
        "log_entry": log_entry
    }

@app.get("/api/v1/foods/log/daily")
async def get_daily_nutrition(target_date: Optional[str] = None):
    # Mock daily nutrition summary
    return {
        "date": target_date or "2024-01-15",
        "actual_calories": 1850,
        "actual_protein_g": 85.5,
        "actual_carbs_g": 220.0,
        "actual_fat_g": 65.2,
        "actual_fiber_g": 28.5,
        "target_calories": 2000,
        "target_protein_g": 100,
        "target_carbs_g": 250,
        "target_fat_g": 70,
        "calories_remaining": 150,
        "protein_remaining_g": 14.5,
        "carbs_remaining_g": 30.0,
        "fat_remaining_g": 4.8,
        "meals": {
            "breakfast": [
                {"food_name": "Oatmeal with berries", "calories": 350, "quantity": 1, "unit": "bowl"}
            ],
            "lunch": [
                {"food_name": "Grilled chicken salad", "calories": 450, "quantity": 1, "unit": "serving"}
            ],
            "dinner": [
                {"food_name": "Salmon with vegetables", "calories": 550, "quantity": 1, "unit": "serving"}
            ],
            "snack": [
                {"food_name": "Greek yogurt", "calories": 150, "quantity": 1, "unit": "cup"}
            ]
        }
    }

# Recommendations endpoints
async def parse_food_with_gemini(description: str) -> dict:
    """Parse food description using Gemini AI."""
    if not GEMINI_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
        return {
            "food_name": description,
            "quantity": 1.0,
            "unit": "serving",
            "confidence": 0.3,
            "source": "fallback"
        }

    try:
        prompt = f"""
        Parse this food description into structured data: "{description}"

        Return JSON with:
        {{
            "food_name": "extracted food name",
            "quantity": number,
            "unit": "unit of measurement",
            "confidence": 0.0-1.0
        }}

        Respond with valid JSON only.
        """

        response = gemini_model.generate_content(prompt)
        content = response.text.strip()

        # Clean up response (remove markdown formatting if present)
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        parsed_data = json.loads(content)
        parsed_data["source"] = "gemini"
        return parsed_data

    except Exception as e:
        print(f"Gemini parsing error: {e}")
        return {
            "food_name": description,
            "quantity": 1.0,
            "unit": "serving",
            "confidence": 0.3,
            "source": "fallback"
        }

@app.post("/api/v1/foods/parse")
async def parse_food_description(description: str):
    """Parse natural language food description using AI."""
    parsed = await parse_food_with_gemini(description)
    return {
        "original_description": description,
        "parsed_data": parsed,
        "gemini_available": GEMINI_AVAILABLE
    }

@app.post("/api/v1/recommendations/generate")
async def generate_recommendations():
    # Enhanced AI recommendations with Gemini integration
    if GEMINI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
        try:
            prompt = """
            Generate 3 personalized nutrition recommendations for a user.
            Return as JSON array with this structure:
            [
                {
                    "id": "unique_id",
                    "recommendation_type": "NUTRIENT_ADJUSTMENT",
                    "title": "recommendation title",
                    "description": "detailed description",
                    "confidence_level": "high",
                    "priority": 1-3,
                    "expected_impact": "high|medium|low",
                    "implementation_difficulty": "easy|medium|hard"
                }
            ]

            Focus on common nutrition improvements like fiber, protein, hydration.
            Respond with valid JSON only.
            """

            response = gemini_model.generate_content(prompt)
            content = response.text.strip()

            # Clean up response
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()

            ai_recommendations = json.loads(content)
            return ai_recommendations

        except Exception as e:
            print(f"Gemini recommendation error: {e}")
            # Fall back to mock data

    # Mock AI recommendations (fallback)
    return [
        {
            "id": "rec_001",
            "recommendation_type": "NUTRIENT_ADJUSTMENT",
            "title": "Increase Fiber Intake",
            "description": "Your current fiber intake is below the recommended daily amount. Increasing fiber can improve digestive health and help with satiety.",
            "confidence_level": "high",
            "priority": 2,
            "expected_impact": "high",
            "implementation_difficulty": "easy",
            "time_horizon": "short_term",
            "nutrient_adjustments": [
                {
                    "nutrient_name": "fiber_g",
                    "current_intake": 18.5,
                    "recommended_intake": 25.0,
                    "adjustment_amount": 6.5,
                    "adjustment_direction": "increase",
                    "unit": "g",
                    "reason": "Current intake is below recommended daily value",
                    "food_sources": ["whole grains", "legumes", "vegetables", "fruits"]
                }
            ],
            "created_at": "2024-01-15T12:00:00Z"
        },
        {
            "id": "rec_002",
            "recommendation_type": "FOOD_SUGGESTION",
            "title": "Add Omega-3 Rich Foods",
            "description": "Include more omega-3 fatty acids in your diet for heart and brain health.",
            "confidence_level": "high",
            "priority": 3,
            "expected_impact": "medium",
            "implementation_difficulty": "medium",
            "time_horizon": "medium_term",
            "food_suggestions": [
                {
                    "food_name": "Salmon",
                    "serving_size": 3.5,
                    "serving_unit": "oz",
                    "calories": 206,
                    "reason": "Excellent source of omega-3 fatty acids",
                    "nutritional_benefits": ["omega-3", "protein", "vitamin D"]
                },
                {
                    "food_name": "Walnuts",
                    "serving_size": 1,
                    "serving_unit": "oz",
                    "calories": 185,
                    "reason": "Plant-based omega-3 source",
                    "nutritional_benefits": ["omega-3", "healthy fats", "protein"]
                }
            ],
            "created_at": "2024-01-15T12:00:00Z"
        }
    ]

@app.get("/api/v1/recommendations/")
async def get_recommendations(active_only: bool = True, limit: int = 10):
    # Return the same mock recommendations
    return await generate_recommendations()

@app.get("/api/v1/recommendations/{recommendation_id}")
async def get_recommendation_details(recommendation_id: str):
    # Mock recommendation details
    return {
        "id": recommendation_id,
        "recommendation_type": "NUTRIENT_ADJUSTMENT",
        "title": "Increase Fiber Intake",
        "description": "Your current fiber intake is below the recommended daily amount. Increasing fiber can improve digestive health and help with satiety.",
        "confidence_level": "high",
        "priority": 2,
        "expected_impact": "high",
        "implementation_difficulty": "easy",
        "time_horizon": "short_term",
        "is_viewed": True,
        "is_accepted": None,
        "user_rating": None,
        "created_at": "2024-01-15T12:00:00Z"
    }

# User profile endpoints
@app.get("/api/v1/users/profile")
async def get_user_profile():
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "first_name": "Demo",
        "last_name": "User",
        "age": 30,
        "gender": "male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "moderately_active",
        "primary_goal": "maintenance",
        "health_conditions": [],
        "dietary_restrictions": [],
        "allergies": []
    }

if __name__ == "__main__":
    print("🚀 Starting Nutrient Recommendation System API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
