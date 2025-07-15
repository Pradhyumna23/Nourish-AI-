"""
Production FastAPI application with real MongoDB Atlas integration.
This version uses persistent MongoDB storage for all data.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import hashlib

# Gemini AI integration
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        GEMINI_AVAILABLE = True
        print(f"✅ Gemini AI configured")
    else:
        GEMINI_AVAILABLE = False
except ImportError as e:
    GEMINI_AVAILABLE = False
    print(f"❌ Gemini import failed: {e}")

# USDA API configuration
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")  # Replace with your actual API key

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nutrient_db")
DATABASE_NAME = "nutrient_recommendation_db"

# Global database client
client = None
db = None

# Create FastAPI app
app = FastAPI(
    title="Nutrient Recommendation System - MongoDB Production",
    description="AI-powered nutrition recommendations with MongoDB Atlas persistence",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://*.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# USDA API Configuration
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Data models
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

class FoodLog(BaseModel):
    fdc_id: int
    food_description: Optional[str] = None
    quantity: float
    unit: str
    meal_type: str
    calories: Optional[float] = None
    protein_g: Optional[float] = 0
    carbs_g: Optional[float] = 0
    fat_g: Optional[float] = 0
    date: Optional[str] = None
    notes: Optional[str] = None

# Database connection functions
async def connect_to_mongo():
    """Connect to MongoDB Atlas."""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        # Create indexes
        await create_indexes()
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def create_indexes():
    """Create database indexes for better performance."""
    try:
        # Users collection indexes
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        
        # Food logs collection indexes
        await db.food_logs.create_index([("user_id", 1), ("date", -1)])
        await db.food_logs.create_index("fdc_id")
        
        # Recommendations collection indexes
        await db.recommendations.create_index([("user_id", 1), ("created_at", -1)])
        
        print("📊 Database indexes created successfully!")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("🔌 Disconnected from MongoDB")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

# USDA API Functions (same as before)
async def search_usda_foods(query: str, page_size: int = 20) -> dict:
    """Search for foods in USDA FoodData Central database."""
    search_url = f"{USDA_BASE_URL}/foods/search"
    
    params = {
        "api_key": USDA_API_KEY,
        "query": query,
        "pageSize": page_size,
        "dataType": ["Foundation", "SR Legacy", "Branded"],
        "sortBy": "dataType.keyword",
        "sortOrder": "asc"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Transform USDA response to our format
            foods = []
            for food in data.get("foods", []):
                # Extract basic nutrients
                nutrients = {}
                for nutrient in food.get("foodNutrients", []):
                    nutrient_id = nutrient.get("nutrientId")
                    amount = nutrient.get("value", 0)
                    
                    # Map common nutrients
                    if nutrient_id == 1008:  # Energy
                        nutrients["calories"] = round(amount, 1)
                    elif nutrient_id == 1003:  # Protein
                        nutrients["protein_g"] = round(amount, 1)
                    elif nutrient_id == 1004:  # Total lipid (fat)
                        nutrients["fat_g"] = round(amount, 1)
                    elif nutrient_id == 1005:  # Carbohydrate
                        nutrients["carbs_g"] = round(amount, 1)
                    elif nutrient_id == 1079:  # Fiber
                        nutrients["fiber_g"] = round(amount, 1)
                    elif nutrient_id == 1093:  # Sodium
                        nutrients["sodium_mg"] = round(amount, 1)
                
                food_item = {
                    "fdc_id": food.get("fdcId"),
                    "description": food.get("description", ""),
                    "brand_owner": food.get("brandOwner", ""),
                    "food_category": food.get("foodCategory", ""),
                    "data_type": food.get("dataType", ""),
                    "nutrients": nutrients
                }
                foods.append(food_item)
            
            return {
                "foods": foods,
                "total_hits": data.get("totalHits", 0),
                "current_page": data.get("currentPage", 1),
                "total_pages": data.get("totalPages", 1)
            }
            
    except Exception as e:
        print(f"USDA API Error: {e}")
        return {
            "foods": [],
            "total_hits": 0,
            "current_page": 1,
            "total_pages": 1
        }

async def get_usda_food_details(fdc_id: int) -> dict:
    """Get detailed nutrition information for a specific food."""
    detail_url = f"{USDA_BASE_URL}/food/{fdc_id}"
    
    params = {"api_key": USDA_API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(detail_url, params=params, timeout=10.0)
            response.raise_for_status()
            
            food = response.json()
            
            # Extract detailed nutrients
            nutrients = {}
            for nutrient in food.get("foodNutrients", []):
                nutrient_name = nutrient.get("nutrient", {}).get("name", "")
                amount = nutrient.get("amount", 0)
                
                # Map nutrients by name
                if "Energy" in nutrient_name:
                    nutrients["calories"] = round(amount, 1)
                elif "Protein" in nutrient_name:
                    nutrients["protein_g"] = round(amount, 1)
                elif "Total lipid" in nutrient_name or "Fat" in nutrient_name:
                    nutrients["fat_g"] = round(amount, 1)
                elif "Carbohydrate" in nutrient_name:
                    nutrients["carbs_g"] = round(amount, 1)
                elif "Fiber" in nutrient_name:
                    nutrients["fiber_g"] = round(amount, 1)
                elif "Sodium" in nutrient_name:
                    nutrients["sodium_mg"] = round(amount, 1)
                elif "Calcium" in nutrient_name:
                    nutrients["calcium_mg"] = round(amount, 1)
                elif "Iron" in nutrient_name:
                    nutrients["iron_mg"] = round(amount, 1)
                elif "Vitamin C" in nutrient_name:
                    nutrients["vitamin_c_mg"] = round(amount, 1)
            
            return {
                "fdc_id": food.get("fdcId"),
                "description": food.get("description", ""),
                "brand_owner": food.get("brandOwner", ""),
                "food_category": food.get("foodCategory", ""),
                "nutrients": nutrients,
                "serving_sizes": [
                    {"unit": "gram", "value": 100.0, "description": "100 grams"},
                    {"unit": "serving", "value": 1.0, "description": "1 serving"}
                ]
            }
            
    except Exception as e:
        print(f"USDA Food Detail Error: {e}")
        return {
            "fdc_id": fdc_id,
            "description": "Food details unavailable",
            "nutrients": {"calories": 200, "protein_g": 8, "carbs_g": 30, "fat_g": 5},
            "serving_sizes": [{"unit": "serving", "value": 1.0}]
        }

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Nutrient Recommendation System - MongoDB Production",
        "version": "3.0.0",
        "status": "running",
        "data_sources": {
            "usda_api": "✅ Real USDA FoodData Central",
            "gemini_ai": "✅ Real Google Gemini AI" if GEMINI_AVAILABLE else "❌ Not available",
            "database": "✅ MongoDB Atlas (Persistent Storage)"
        }
    }

@app.get("/health")
async def health_check():
    # Test database connection
    db_status = "✅ Connected"
    try:
        await client.admin.command('ping')
    except:
        db_status = "❌ Disconnected"
    
    return {
        "status": "healthy",
        "message": "MongoDB Production API running",
        "database": db_status,
        "usda_api_available": True,
        "gemini_available": GEMINI_AVAILABLE
    }

# Diverse Food Database for Recommendations
async def get_diverse_food_recommendations(target_nutrients, dietary_restrictions, allergies, meal_type, limit):
    """Generate diverse food recommendations with rotation to avoid repetition."""
    import random
    from datetime import datetime

    # Comprehensive food database organized by nutrients and categories
    DIVERSE_FOOD_DATABASE = {
        "protein": {
            "animal": [
                {
                    "food_name": "Salmon (Atlantic, Wild)",
                    "serving_size": 3.5, "serving_unit": "oz", "calories_per_serving": 206,
                    "key_nutrients": {"protein_g": 25.4, "fat_g": 12.4, "omega3_g": 2.3},
                    "reason": "Rich in omega-3 fatty acids and complete protein",
                    "category": "fish", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Turkey Breast (Lean)",
                    "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 125,
                    "key_nutrients": {"protein_g": 26, "fat_g": 1.8, "selenium_mcg": 27.4},
                    "reason": "Lean protein with selenium for immune function",
                    "category": "poultry", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Eggs (Large, Whole)",
                    "serving_size": 2, "serving_unit": "eggs", "calories_per_serving": 140,
                    "key_nutrients": {"protein_g": 12.6, "fat_g": 10, "choline_mg": 294},
                    "reason": "Complete protein with brain-healthy choline",
                    "category": "eggs", "meal_timing": ["breakfast", "lunch"]
                },
                {
                    "food_name": "Lean Beef (Sirloin)",
                    "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 158,
                    "key_nutrients": {"protein_g": 26, "iron_mg": 2.9, "zinc_mg": 4.5},
                    "reason": "High in heme iron and zinc for energy and immunity",
                    "category": "red_meat", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Tuna (Yellowfin, Fresh)",
                    "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 109,
                    "key_nutrients": {"protein_g": 25, "fat_g": 1, "niacin_mg": 18.8},
                    "reason": "Very lean protein with B vitamins for energy metabolism",
                    "category": "fish", "meal_timing": ["lunch", "dinner"]
                }
            ],
            "plant": [
                {
                    "food_name": "Lentils (Cooked)",
                    "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 230,
                    "key_nutrients": {"protein_g": 18, "fiber_g": 15.6, "folate_mcg": 358},
                    "reason": "Plant protein with fiber and folate for heart health",
                    "category": "legumes", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Quinoa (Cooked)",
                    "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 222,
                    "key_nutrients": {"protein_g": 8, "fiber_g": 5.2, "magnesium_mg": 118},
                    "reason": "Complete plant protein with essential amino acids",
                    "category": "grains", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Hemp Seeds",
                    "serving_size": 3, "serving_unit": "tbsp", "calories_per_serving": 170,
                    "key_nutrients": {"protein_g": 10, "omega3_g": 2.6, "magnesium_mg": 210},
                    "reason": "Complete protein with healthy fats and minerals",
                    "category": "seeds", "meal_timing": ["breakfast", "snack"]
                },
                {
                    "food_name": "Chickpeas (Cooked)",
                    "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 269,
                    "key_nutrients": {"protein_g": 14.5, "fiber_g": 12.5, "folate_mcg": 282},
                    "reason": "High protein legume with fiber for digestive health",
                    "category": "legumes", "meal_timing": ["lunch", "dinner"]
                },
                {
                    "food_name": "Tofu (Firm)",
                    "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 94,
                    "key_nutrients": {"protein_g": 10, "calcium_mg": 253, "isoflavones_mg": 25},
                    "reason": "Versatile plant protein with calcium and phytonutrients",
                    "category": "soy", "meal_timing": ["lunch", "dinner"]
                }
            ],
            "dairy": [
                {
                    "food_name": "Greek Yogurt (Plain, 2%)",
                    "serving_size": 6, "serving_unit": "oz", "calories_per_serving": 100,
                    "key_nutrients": {"protein_g": 15, "calcium_mg": 200, "probiotics": "yes"},
                    "reason": "Probiotic protein source for gut and bone health",
                    "category": "dairy", "meal_timing": ["breakfast", "snack"]
                },
                {
                    "food_name": "Cottage Cheese (Low-fat)",
                    "serving_size": 0.5, "serving_unit": "cup", "calories_per_serving": 81,
                    "key_nutrients": {"protein_g": 14, "calcium_mg": 69, "phosphorus_mg": 151},
                    "reason": "Casein protein for sustained amino acid release",
                    "category": "dairy", "meal_timing": ["breakfast", "snack"]
                }
            ]
        },
        "iron": [
            {
                "food_name": "Beef Liver (Cooked)",
                "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 149,
                "key_nutrients": {"iron_mg": 18, "vitamin_a_iu": 16898, "folate_mcg": 215},
                "reason": "Highest bioavailable iron source with vitamin A",
                "category": "organ_meat", "meal_timing": ["lunch", "dinner"]
            },
            {
                "food_name": "Pumpkin Seeds",
                "serving_size": 1, "serving_unit": "oz", "calories_per_serving": 151,
                "key_nutrients": {"iron_mg": 4.2, "zinc_mg": 2.2, "magnesium_mg": 150},
                "reason": "Plant-based iron with zinc and magnesium",
                "category": "seeds", "meal_timing": ["snack", "breakfast"]
            },
            {
                "food_name": "Dark Chocolate (70% Cacao)",
                "serving_size": 1, "serving_unit": "oz", "calories_per_serving": 170,
                "key_nutrients": {"iron_mg": 3.9, "magnesium_mg": 64, "antioxidants": "high"},
                "reason": "Iron-rich treat with antioxidants and magnesium",
                "category": "treats", "meal_timing": ["snack", "dessert"]
            },
            {
                "food_name": "Oysters (Cooked)",
                "serving_size": 3, "serving_unit": "oz", "calories_per_serving": 67,
                "key_nutrients": {"iron_mg": 5.1, "zinc_mg": 32, "vitamin_b12_mcg": 13.8},
                "reason": "Exceptional iron and zinc source from the sea",
                "category": "shellfish", "meal_timing": ["lunch", "dinner"]
            }
        ]
    }

    # Add more nutrient categories
    DIVERSE_FOOD_DATABASE.update({
        "fiber": [
            {
                "food_name": "Avocado (Medium)",
                "serving_size": 0.5, "serving_unit": "avocado", "calories_per_serving": 160,
                "key_nutrients": {"fiber_g": 6.7, "potassium_mg": 345, "folate_mcg": 59},
                "reason": "Healthy fats with fiber and potassium for heart health",
                "category": "fruits", "meal_timing": ["breakfast", "lunch"]
            },
            {
                "food_name": "Chia Seeds",
                "serving_size": 2, "serving_unit": "tbsp", "calories_per_serving": 138,
                "key_nutrients": {"fiber_g": 9.8, "omega3_g": 4.9, "calcium_mg": 179},
                "reason": "Superfood with fiber, omega-3s, and calcium",
                "category": "seeds", "meal_timing": ["breakfast", "snack"]
            },
            {
                "food_name": "Raspberries (Fresh)",
                "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 64,
                "key_nutrients": {"fiber_g": 8, "vitamin_c_mg": 32, "antioxidants": "very_high"},
                "reason": "High fiber fruit with vitamin C and antioxidants",
                "category": "berries", "meal_timing": ["breakfast", "snack"]
            }
        ],
        "calcium": [
            {
                "food_name": "Sardines (Canned with Bones)",
                "serving_size": 3.75, "serving_unit": "oz", "calories_per_serving": 191,
                "key_nutrients": {"calcium_mg": 351, "protein_g": 23, "omega3_g": 1.4},
                "reason": "Calcium from bones plus protein and omega-3s",
                "category": "fish", "meal_timing": ["lunch", "dinner"]
            },
            {
                "food_name": "Kale (Raw)",
                "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 33,
                "key_nutrients": {"calcium_mg": 90, "vitamin_k_mcg": 547, "vitamin_c_mg": 80},
                "reason": "Plant calcium with vitamins K and C for bone health",
                "category": "leafy_greens", "meal_timing": ["lunch", "dinner"]
            }
        ],
        "vitamin_c": [
            {
                "food_name": "Red Bell Pepper (Raw)",
                "serving_size": 1, "serving_unit": "medium", "calories_per_serving": 37,
                "key_nutrients": {"vitamin_c_mg": 152, "vitamin_a_iu": 3726, "fiber_g": 3.1},
                "reason": "Vitamin C powerhouse with vitamin A and fiber",
                "category": "vegetables", "meal_timing": ["lunch", "snack"]
            },
            {
                "food_name": "Strawberries (Fresh)",
                "serving_size": 1, "serving_unit": "cup", "calories_per_serving": 49,
                "key_nutrients": {"vitamin_c_mg": 89, "fiber_g": 3, "antioxidants": "high"},
                "reason": "Sweet vitamin C source with antioxidants",
                "category": "berries", "meal_timing": ["breakfast", "snack"]
            }
        ]
    })

    # Get user's recent recommendations to avoid repetition
    user = await db.users.find_one({}, sort=[("created_at", -1)])
    recent_foods = []
    if user:
        # Get foods recommended in last 3 days
        recent_recs = await db.food_recommendations.find({
            "user_id": str(user["_id"]),
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=3)}
        }).to_list(length=50)
        recent_foods = [rec.get("food_name", "") for rec in recent_recs]

    selected_foods = []

    # Select diverse foods for each target nutrient
    for nutrient in target_nutrients:
        if nutrient in DIVERSE_FOOD_DATABASE:
            nutrient_foods = DIVERSE_FOOD_DATABASE[nutrient]

            # Handle nested structure for protein
            if isinstance(nutrient_foods, dict):
                all_foods = []
                for category, foods in nutrient_foods.items():
                    # Filter based on dietary restrictions
                    if "vegetarian" in dietary_restrictions and category == "animal":
                        continue
                    if "vegan" in dietary_restrictions and category in ["animal", "dairy"]:
                        continue
                    all_foods.extend(foods)
                nutrient_foods = all_foods

            # Filter out recently recommended foods
            available_foods = [food for food in nutrient_foods
                             if food["food_name"] not in recent_foods]

            # If all foods were recent, use all foods but shuffle
            if not available_foods:
                available_foods = nutrient_foods

            # Filter by allergies
            safe_foods = []
            for food in available_foods:
                is_safe = True
                food_name_lower = food["food_name"].lower()
                for allergy in allergies:
                    allergy_name = allergy if isinstance(allergy, str) else allergy.get('allergy', '')
                    if allergy_name.lower() in food_name_lower:
                        is_safe = False
                        break
                if is_safe:
                    safe_foods.append(food)

            # Randomly select foods to ensure variety
            if safe_foods:
                random.shuffle(safe_foods)
                selected_foods.extend(safe_foods[:2])  # Take 2 foods per nutrient

    # If no specific nutrients, provide general healthy foods
    if not selected_foods:
        general_foods = [
            {
                "food_name": "Mixed Nuts (Unsalted)",
                "serving_size": 1, "serving_unit": "oz", "calories_per_serving": 173,
                "key_nutrients": {"protein_g": 5, "fiber_g": 3, "healthy_fats_g": 15},
                "reason": "Balanced nutrition with protein, fiber, and healthy fats",
                "category": "nuts", "meal_timing": ["snack"]
            },
            {
                "food_name": "Sweet Potato (Baked)",
                "serving_size": 1, "serving_unit": "medium", "calories_per_serving": 112,
                "key_nutrients": {"vitamin_a_iu": 21909, "fiber_g": 3.9, "potassium_mg": 542},
                "reason": "Complex carbs with vitamin A and potassium",
                "category": "vegetables", "meal_timing": ["lunch", "dinner"]
            }
        ]
        selected_foods = general_foods

    # Store recommendations to track for future diversity
    if user and selected_foods:
        for food in selected_foods[:limit]:
            await db.food_recommendations.insert_one({
                "user_id": str(user["_id"]),
                "food_name": food["food_name"],
                "target_nutrients": target_nutrients,
                "created_at": datetime.utcnow()
            })

    # Shuffle and limit results
    random.shuffle(selected_foods)
    return selected_foods[:limit]

# Nutrient-based Food Recommendations (must come before {fdc_id} route)
@app.get("/api/v1/foods/recommendations")
async def get_food_recommendations_by_nutrients(
    target_nutrients: Optional[str] = None,
    exclude_allergens: Optional[str] = None,
    dietary_restrictions: Optional[str] = None,
    meal_type: Optional[str] = None,
    limit: int = 10
):
    """Get food recommendations based on specific nutrient needs."""
    try:
        # Get current user and their nutrition data
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_profile = serialize_doc(user) if user else {}
        daily_nutrition = await get_daily_nutrition()

        # Parse parameters
        target_nutrients_list = target_nutrients.split(',') if target_nutrients else []
        exclude_allergens_list = exclude_allergens.split(',') if exclude_allergens else []
        dietary_restrictions_list = dietary_restrictions.split(',') if dietary_restrictions else []

        # Add user's allergies and dietary restrictions
        if user:
            # Handle allergies - they might be strings or objects
            allergies = user.get('allergies', [])
            for allergy in allergies:
                if isinstance(allergy, str):
                    exclude_allergens_list.append(allergy)
                elif isinstance(allergy, dict):
                    exclude_allergens_list.append(allergy.get('allergy', ''))

            dietary_restrictions_list.extend([dr.get('type', '') for dr in user.get('dietary_restrictions', [])])

        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                # Analyze current nutrient gaps
                nutrient_gaps = []

                # Calculate major nutrient gaps
                calorie_gap = daily_nutrition.get('target_calories', 2000) - daily_nutrition.get('actual_calories', 0)
                protein_gap = daily_nutrition.get('target_protein_g', 100) - daily_nutrition.get('actual_protein_g', 0)

                if calorie_gap > 200:
                    nutrient_gaps.append(f"calories (need {calorie_gap:.0f} more)")
                if protein_gap > 10:
                    nutrient_gaps.append(f"protein (need {protein_gap:.0f}g more)")

                # Add specific nutrients if requested
                if target_nutrients_list:
                    nutrient_gaps.extend(target_nutrients_list)

                prompt = f"""
                You are a nutrition expert. Recommend specific foods to address these nutrient needs:

                User Profile:
                - Age: {user_profile.get('age', 'unknown')}
                - Gender: {user_profile.get('gender', 'unknown')}
                - Activity Level: {user_profile.get('activity_level', 'unknown')}
                - Primary Goal: {user_profile.get('primary_goal', 'unknown')}

                Current Nutrient Gaps: {', '.join(nutrient_gaps) if nutrient_gaps else 'general nutrition optimization'}

                Dietary Restrictions: {', '.join(dietary_restrictions_list) if dietary_restrictions_list else 'none'}
                Allergies to Avoid: {', '.join(exclude_allergens_list) if exclude_allergens_list else 'none'}
                Preferred Meal Type: {meal_type or 'any'}

                Provide {limit} specific food recommendations that address the nutrient gaps.

                Return as JSON array:
                [
                    {{
                        "food_name": "Specific food name",
                        "serving_size": number,
                        "serving_unit": "cup|oz|gram|piece|tablespoon",
                        "calories_per_serving": number,
                        "key_nutrients": {{
                            "protein_g": number,
                            "carbs_g": number,
                            "fat_g": number,
                            "fiber_g": number,
                            "iron_mg": number,
                            "calcium_mg": number,
                            "vitamin_c_mg": number
                        }},
                        "addresses_nutrients": ["nutrient1", "nutrient2"],
                        "reason": "Why this food is recommended for your needs",
                        "nutritional_benefits": ["benefit1", "benefit2", "benefit3"],
                        "preparation_suggestions": ["suggestion1", "suggestion2"],
                        "best_meal_timing": "breakfast|lunch|dinner|snack",
                        "pairs_well_with": ["food1", "food2"],
                        "cost_effectiveness": "budget_friendly|moderate|premium"
                    }}
                ]

                Focus on nutrient-dense, whole foods. Respond with valid JSON only.
                """

                response = gemini_model.generate_content(prompt)
                content = response.text.strip()

                # Clean up response
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()

                food_recommendations = json.loads(content)

                print(f"✅ Generated {len(food_recommendations)} nutrient-based food recommendations")
                return {
                    "recommendations": food_recommendations,
                    "user_context": {
                        "nutrient_gaps": nutrient_gaps,
                        "dietary_restrictions": dietary_restrictions_list,
                        "allergies": exclude_allergens_list,
                        "meal_type": meal_type
                    },
                    "source": "gemini_ai"
                }

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse Gemini food recommendations JSON: {e}")
            except Exception as e:
                print(f"❌ Gemini food recommendation error: {e}")

        # Fallback: Rule-based food recommendations with variety
        print("🔄 Generating diverse fallback food recommendations...")

        fallback_foods = await get_diverse_food_recommendations(
            target_nutrients_list,
            dietary_restrictions_list,
            exclude_allergens_list,
            meal_type,
            limit
        )

        return {
            "recommendations": fallback_foods,
            "user_context": {
                "nutrient_gaps": target_nutrients_list,
                "dietary_restrictions": dietary_restrictions_list,
                "allergies": exclude_allergens_list,
                "meal_type": meal_type
            },
            "source": "diverse_rule_based"
        }

    except Exception as e:
        print(f"Food recommendations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate food recommendations")

# Real USDA Food Search
@app.get("/api/v1/foods/search")
async def search_foods(query: str, page_size: int = 20):
    """Search for foods using real USDA database."""
    result = await search_usda_foods(query, page_size)
    return result

@app.get("/api/v1/foods/{fdc_id}")
async def get_food_details(fdc_id: int):
    """Get detailed food information from USDA database."""
    result = await get_usda_food_details(fdc_id)
    return result

# Enhanced Gemini food parsing
@app.post("/api/v1/foods/parse")
async def parse_food_description(description: str):
    """Parse food description using Gemini AI with real USDA integration."""

    # First, try Gemini parsing
    parsed_data = {"food_name": description, "quantity": 1.0, "unit": "serving", "confidence": 0.3}

    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            prompt = f"""
            Parse this food description: "{description}"

            Extract:
            1. Food name (for USDA search)
            2. Quantity (number)
            3. Unit of measurement

            Return JSON:
            {{
                "food_name": "clean food name for database search",
                "quantity": number,
                "unit": "unit",
                "confidence": 0.0-1.0,
                "search_terms": ["alternative", "terms"]
            }}

            Respond with valid JSON only.
            """

            response = gemini_model.generate_content(prompt)
            content = response.text.strip()

            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()

            parsed_data = json.loads(content)
            parsed_data["source"] = "gemini"

        except Exception as e:
            print(f"Gemini parsing error: {e}")

    # If we have a good parse, try to find the food in USDA database
    usda_results = None
    if parsed_data.get("confidence", 0) > 0.5:
        try:
            usda_results = await search_usda_foods(parsed_data["food_name"], 3)
        except Exception as e:
            print(f"USDA search error: {e}")

    return {
        "original_description": description,
        "parsed_data": parsed_data,
        "usda_matches": usda_results.get("foods", [])[:3] if usda_results else [],
        "gemini_available": GEMINI_AVAILABLE
    }

# MongoDB-backed Auth endpoints
@app.post("/api/v1/auth/register")
async def register(user: UserCreate):
    """Register a new user with MongoDB storage."""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"username": user.username},
                {"email": user.email}
            ]
        })

        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")

        # Create new user document
        user_doc = {
            "username": user.username,
            "email": user.email,
            "password_hash": hash_password(user.password),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "age": user.age,
            "gender": user.gender,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "activity_level": None,
            "primary_goal": None,
            "health_conditions": [],
            "dietary_restrictions": [],
            "allergies": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert user into database
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        # Return user data (without password hash)
        user_response = serialize_doc(user_doc)
        user_response.pop("password_hash", None)

        return {
            "message": "User registered successfully",
            "user": user_response
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/auth/token")
async def login(credentials: UserLogin):
    """Login user with MongoDB verification."""
    try:
        # Find user by username
        user = await db.users.find_one({"username": credentials.username})

        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Return token and user data (without password hash)
        user_response = serialize_doc(user)
        user_response.pop("password_hash", None)

        return {
            "access_token": f"token_{user['_id']}_{datetime.now().timestamp()}",
            "token_type": "bearer",
            "user": user_response
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/api/v1/auth/me")
async def get_current_user():
    """Get current user info (demo version)."""
    # In production, extract user from JWT token
    user = await db.users.find_one({}, sort=[("created_at", -1)])
    if user:
        user_response = serialize_doc(user)
        user_response.pop("password_hash", None)
        return user_response

    # Fallback demo user
    return {
        "id": "demo_user_id",
        "username": "demo_user",
        "email": "demo@example.com",
        "first_name": "Demo",
        "last_name": "User"
    }

# MongoDB-backed User Profile Management
@app.get("/api/v1/users/profile")
async def get_user_profile():
    """Get user profile from MongoDB."""
    try:
        # In production, get user_id from JWT token
        # For demo, get the most recent user
        user = await db.users.find_one({}, sort=[("created_at", -1)])

        if user:
            user_response = serialize_doc(user)
            user_response.pop("password_hash", None)
            return user_response

        # Fallback demo profile
        return {
            "id": "demo_user_id",
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

    except Exception as e:
        print(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@app.put("/api/v1/users/profile")
async def update_user_profile(profile_data: dict):
    """Update user profile in MongoDB."""
    try:
        # In production, get user_id from JWT token
        # For demo, update the most recent user
        user = await db.users.find_one({}, sort=[("created_at", -1)])

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()
        }

        # Update allowed fields
        allowed_fields = [
            "first_name", "last_name", "email", "age", "gender",
            "height_cm", "weight_kg", "activity_level", "primary_goal",
            "target_calories"
        ]

        for field in allowed_fields:
            if field in profile_data:
                update_data[field] = profile_data[field]

        # Update user in database
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )

        # Fetch and return updated user
        updated_user = await db.users.find_one({"_id": user["_id"]})
        user_response = serialize_doc(updated_user)
        user_response.pop("password_hash", None)

        print(f"✅ Profile updated for user: {user_response.get('username')}")
        return user_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Health conditions management
@app.post("/api/v1/users/health-conditions")
async def add_health_condition(condition: dict):
    """Add health condition to user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add condition to user's health_conditions array
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$push": {"health_conditions": condition},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Health condition added: {condition}")
        return {"message": "Health condition added successfully", "condition": condition}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Add health condition error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add health condition")

@app.delete("/api/v1/users/health-conditions/{condition_name}")
async def remove_health_condition(condition_name: str):
    """Remove health condition from user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove condition from user's health_conditions array
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$pull": {"health_conditions": {"name": condition_name}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Health condition removed: {condition_name}")
        return {"message": "Health condition removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Remove health condition error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove health condition")

# Dietary restrictions management
@app.post("/api/v1/users/dietary-restrictions")
async def add_dietary_restriction(restriction: dict):
    """Add dietary restriction to user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$push": {"dietary_restrictions": restriction},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Dietary restriction added: {restriction}")
        return {"message": "Dietary restriction added successfully", "restriction": restriction}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Add dietary restriction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add dietary restriction")

@app.delete("/api/v1/users/dietary-restrictions/{restriction_type}")
async def remove_dietary_restriction(restriction_type: str):
    """Remove dietary restriction from user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$pull": {"dietary_restrictions": {"type": restriction_type}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Dietary restriction removed: {restriction_type}")
        return {"message": "Dietary restriction removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Remove dietary restriction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove dietary restriction")

# Allergies management
@app.post("/api/v1/users/allergies")
async def add_allergy(allergy_data: dict):
    """Add allergy to user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Extract the allergy string from the data
        allergy = allergy_data.get("allergy", "").strip()
        if not allergy:
            raise HTTPException(status_code=400, detail="Allergy name is required")

        # Store only the string, not the object
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$push": {"allergies": allergy},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Allergy added: {allergy}")
        return {"message": "Allergy added successfully", "allergy": allergy}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Add allergy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add allergy")

@app.delete("/api/v1/users/allergies/{allergy}")
async def remove_allergy(allergy: str):
    """Remove allergy from user profile."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$pull": {"allergies": allergy},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        print(f"✅ Allergy removed: {allergy}")
        return {"message": "Allergy removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Remove allergy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove allergy")

@app.post("/api/v1/users/fix-allergies")
async def fix_allergies():
    """Fix allergy data format - convert objects to strings."""
    try:
        users = await db.users.find({}).to_list(length=None)
        fixed_count = 0

        for user in users:
            allergies = user.get('allergies', [])
            if not allergies:
                continue

            # Check if any allergies are objects
            needs_fix = any(isinstance(allergy, dict) for allergy in allergies)

            if needs_fix:
                # Convert all allergies to strings
                fixed_allergies = []
                for allergy in allergies:
                    if isinstance(allergy, str):
                        fixed_allergies.append(allergy)
                    elif isinstance(allergy, dict):
                        allergy_name = allergy.get('allergy', '')
                        if allergy_name:
                            fixed_allergies.append(allergy_name)

                # Update the user
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "allergies": fixed_allergies,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                fixed_count += 1
                print(f"✅ Fixed allergies for user {user['_id']}: {fixed_allergies}")

        return {
            "message": f"Fixed allergy data for {fixed_count} users",
            "fixed_count": fixed_count
        }

    except Exception as e:
        print(f"Fix allergies error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fix allergy data")

# Helper function to get food details from USDA API
async def get_food_details_from_usda(fdc_id: int):
    """Get food details from USDA API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}")
            if response.status_code == 200:
                data = response.json()

                # Extract nutrients
                nutrients = {}
                for nutrient in data.get("foodNutrients", []):
                    nutrient_name = nutrient.get("nutrient", {}).get("name", "").lower()
                    amount = nutrient.get("amount", 0)

                    if "energy" in nutrient_name or "calorie" in nutrient_name:
                        nutrients["calories"] = amount
                    elif "protein" in nutrient_name:
                        nutrients["protein_g"] = amount
                    elif "carbohydrate" in nutrient_name:
                        nutrients["carbs_g"] = amount
                    elif "total lipid" in nutrient_name or "fat" in nutrient_name:
                        nutrients["fat_g"] = amount

                return {
                    "description": data.get("description", ""),
                    "nutrients": nutrients
                }
    except Exception as e:
        print(f"Error fetching food details from USDA: {e}")
    return None

# MongoDB-backed Food Logging
@app.post("/api/v1/foods/log")
async def log_food(food_log: FoodLog):
    """Log food entry to MongoDB."""
    try:
        # Get current user (in production, from JWT token)
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Get food details from USDA API if not provided
        food_description = food_log.food_description
        calories = food_log.calories
        protein_g = food_log.protein_g or 0
        carbs_g = food_log.carbs_g or 0
        fat_g = food_log.fat_g or 0

        if not food_description or not calories:
            try:
                # Fetch food details from USDA API
                food_details = await get_food_details_from_usda(food_log.fdc_id)
                if food_details:
                    food_description = food_details.get("description", f"Food ID {food_log.fdc_id}")

                    # Calculate nutrition based on quantity (simplified calculation)
                    base_nutrients = food_details.get("nutrients", {})
                    # Assume 1 serving = 100g for calculation purposes
                    serving_factor = food_log.quantity if food_log.unit in ['gram', 'g'] else food_log.quantity
                    if food_log.unit == 'serving':
                        serving_factor = food_log.quantity * 1.0  # 1 serving factor
                    elif food_log.unit in ['cup', 'cups']:
                        serving_factor = food_log.quantity * 2.0  # Approximate factor
                    else:
                        serving_factor = food_log.quantity * 1.0

                    calories = (base_nutrients.get("calories", 0) * serving_factor) if not calories else calories
                    protein_g = (base_nutrients.get("protein_g", 0) * serving_factor) if not food_log.protein_g else protein_g
                    carbs_g = (base_nutrients.get("carbs_g", 0) * serving_factor) if not food_log.carbs_g else carbs_g
                    fat_g = (base_nutrients.get("fat_g", 0) * serving_factor) if not food_log.fat_g else fat_g
                else:
                    food_description = f"Food ID {food_log.fdc_id}"
            except Exception as e:
                print(f"Warning: Could not fetch food details for FDC ID {food_log.fdc_id}: {e}")
                food_description = f"Food ID {food_log.fdc_id}"

        # Use provided date or current date
        log_date = food_log.date if food_log.date else datetime.now().strftime("%Y-%m-%d")
        if isinstance(log_date, str) and 'T' in log_date:
            # Parse ISO datetime string to date
            log_date = datetime.fromisoformat(log_date.replace('Z', '+00:00')).strftime("%Y-%m-%d")

        # Create food log document
        log_doc = {
            "user_id": user_id,
            "fdc_id": food_log.fdc_id,
            "food_description": food_description,
            "quantity": food_log.quantity,
            "unit": food_log.unit,
            "meal_type": food_log.meal_type,
            "calories": round(calories, 1) if calories else 0,
            "protein_g": round(protein_g, 1),
            "carbs_g": round(carbs_g, 1),
            "fat_g": round(fat_g, 1),
            "date": log_date,
            "notes": food_log.notes,
            "logged_at": datetime.utcnow()
        }

        # Insert into database
        result = await db.food_logs.insert_one(log_doc)
        log_doc["_id"] = result.inserted_id

        log_response = serialize_doc(log_doc)
        print(f"✅ Food logged: {food_description} - {food_log.quantity} {food_log.unit}")

        return {
            "message": "Food logged successfully",
            "log_entry": log_response
        }

    except Exception as e:
        print(f"Food logging error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log food: {str(e)}")


@app.get("/api/v1/foods/log/daily")
async def get_daily_nutrition(target_date: Optional[str] = None):
    """Get daily nutrition summary for a specific date."""
    try:
        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Use provided date or current date
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # Get all food logs for the date
        food_logs = await db.food_logs.find({
            "user_id": user_id,
            "date": target_date
        }).to_list(length=None)

        # Calculate totals
        total_calories = sum(log.get("calories", 0) for log in food_logs)
        total_protein = sum(log.get("protein_g", 0) for log in food_logs)
        total_carbs = sum(log.get("carbs_g", 0) for log in food_logs)
        total_fat = sum(log.get("fat_g", 0) for log in food_logs)

        # Group by meal type
        meals = {}
        for log in food_logs:
            meal_type = log.get("meal_type", "other")
            if meal_type not in meals:
                meals[meal_type] = []
            meals[meal_type].append(serialize_doc(log))

        return {
            "date": target_date,
            "total_calories": round(total_calories, 1),
            "total_protein_g": round(total_protein, 1),
            "total_carbs_g": round(total_carbs, 1),
            "total_fat_g": round(total_fat, 1),
            "meals": meals,
            "food_count": len(food_logs)
        }

    except Exception as e:
        print(f"Daily nutrition error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily nutrition: {str(e)}")


@app.get("/api/v1/foods/log/history")
async def get_food_log_history(days: int = 7):
    """Get food log history for the current user."""
    try:
        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")

        # Get food logs
        food_logs = await db.food_logs.find({
            "user_id": user_id,
            "date": {"$gte": start_date_str}
        }).sort("logged_at", -1).to_list(length=None)

        # Serialize and return
        return [serialize_doc(log) for log in food_logs]

    except Exception as e:
        print(f"Food history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get food history: {str(e)}")


@app.get("/api/v1/nutrition/recommendations")
async def get_nutrition_recommendations(target_date: Optional[str] = None):
    """Get personalized nutrition recommendations based on current intake."""
    try:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Get current day's nutrition
        daily_nutrition = await get_daily_nutrition(target_date)

        # Calculate what's needed for the rest of the day
        remaining = daily_nutrition["remaining"]
        targets = daily_nutrition["targets"]
        actual = daily_nutrition["summary"]

        recommendations = []

        # Calorie recommendations with safety checks
        if remaining["calories"] > 300:
            safe_calorie_foods = get_safe_food_suggestions(user, "calories", remaining["calories"])
            recommendations.append({
                "type": "meal_suggestion",
                "priority": "high",
                "title": "Add a Balanced Meal",
                "description": f"You have {round(remaining['calories'])} calories remaining. Consider a balanced meal with protein, carbs, and healthy fats.",
                "suggested_foods": safe_calorie_foods,
                "safety_note": "Meal suggestions customized for your dietary restrictions and health conditions."
            })
        elif remaining["calories"] < -200:
            recommendations.append({
                "type": "activity_suggestion",
                "priority": "medium",
                "title": "Consider Light Activity",
                "description": f"You're {round(abs(remaining['calories']))} calories over target. A 30-minute walk could help balance your intake.",
                "suggested_activities": [
                    {"name": "Brisk walk", "duration": "30 minutes", "calories_burned": 150},
                    {"name": "Light cycling", "duration": "20 minutes", "calories_burned": 200}
                ]
            })

        # Protein recommendations with safety checks
        if remaining["protein_g"] > 20:
            safe_protein_foods = get_safe_food_suggestions(user, "protein", remaining["protein_g"])
            recommendations.append({
                "type": "nutrient_focus",
                "priority": "high",
                "title": "Increase Protein Intake",
                "description": f"You need {round(remaining['protein_g'])}g more protein today.",
                "suggested_foods": safe_protein_foods,
                "safety_note": "Suggestions filtered based on your dietary restrictions and health conditions."
            })

        # Fiber recommendations with safety checks
        fiber_target = targets.get("fiber_g", 25)
        if actual["actual_fiber_g"] < fiber_target * 0.7:
            safe_fiber_foods = get_safe_food_suggestions(user, "fiber", fiber_target - actual["actual_fiber_g"])
            recommendations.append({
                "type": "nutrient_focus",
                "priority": "medium",
                "title": "Boost Fiber Intake",
                "description": f"Aim for {round(fiber_target - actual['actual_fiber_g'])}g more fiber for digestive health.",
                "suggested_foods": safe_fiber_foods,
                "safety_note": "High-fiber foods selected based on your dietary preferences and restrictions."
            })

        # Hydration reminder
        recommendations.append({
            "type": "hydration",
            "priority": "low",
            "title": "Stay Hydrated",
            "description": "Aim for 8-10 glasses of water throughout the day, especially if you're active.",
            "suggested_amount": "2-3 more glasses"
        })

        # Goal-specific recommendations
        primary_goal = user.get("primary_goal", "maintenance") if user else "maintenance"
        if primary_goal == "muscle_gain":
            recommendations.append({
                "type": "goal_specific",
                "priority": "high",
                "title": "Post-Workout Nutrition",
                "description": "For muscle gain, consume protein within 2 hours after workouts.",
                "suggested_timing": "Within 2 hours post-workout",
                "suggested_foods": [
                    {"name": "Protein shake with banana", "protein_g": 25},
                    {"name": "Chocolate milk", "protein_g": 8, "carbs_g": 26}
                ]
            })
        elif primary_goal == "weight_loss":
            recommendations.append({
                "type": "goal_specific",
                "priority": "medium",
                "title": "Satiety Focus",
                "description": "Choose high-volume, low-calorie foods to stay satisfied while in a calorie deficit.",
                "suggested_foods": [
                    {"name": "Large salad with lean protein", "calories": 200},
                    {"name": "Vegetable soup", "calories": 150},
                    {"name": "Cucumber and hummus", "calories": 100}
                ]
            })

        return {
            "date": target_date,
            "recommendations": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "high"]),
                "calories_remaining": remaining["calories"],
                "protein_remaining": remaining["protein_g"]
            }
        }

    except Exception as e:
        print(f"Nutrition recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get nutrition recommendations: {str(e)}")


@app.get("/api/v1/nutrition/weekly-summary")
async def get_weekly_nutrition_summary(weeks: int = 1):
    """Get weekly nutrition summary with trends and insights."""
    try:
        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=weeks * 7)

        # Get all food logs in the date range
        food_logs = await db.food_logs.find({
            "user_id": user_id,
            "date": {"$gte": start_date.strftime("%Y-%m-%d")}
        }).to_list(length=None)

        # Group by date
        daily_summaries = {}
        for log in food_logs:
            date = log.get("date")
            if date not in daily_summaries:
                daily_summaries[date] = {
                    "calories": 0,
                    "protein_g": 0,
                    "carbs_g": 0,
                    "fat_g": 0,
                    "fiber_g": 0,
                    "food_count": 0
                }

            daily_summaries[date]["calories"] += float(log.get("calories", 0) or 0)
            daily_summaries[date]["protein_g"] += float(log.get("protein_g", 0) or 0)
            daily_summaries[date]["carbs_g"] += float(log.get("carbs_g", 0) or 0)
            daily_summaries[date]["fat_g"] += float(log.get("fat_g", 0) or 0)
            daily_summaries[date]["fiber_g"] += float(log.get("fiber_g", 0) or 0)
            daily_summaries[date]["food_count"] += 1

        # Calculate averages
        days_with_data = len(daily_summaries)
        if days_with_data > 0:
            avg_calories = sum(day["calories"] for day in daily_summaries.values()) / days_with_data
            avg_protein = sum(day["protein_g"] for day in daily_summaries.values()) / days_with_data
            avg_carbs = sum(day["carbs_g"] for day in daily_summaries.values()) / days_with_data
            avg_fat = sum(day["fat_g"] for day in daily_summaries.values()) / days_with_data
            avg_fiber = sum(day["fiber_g"] for day in daily_summaries.values()) / days_with_data
        else:
            avg_calories = avg_protein = avg_carbs = avg_fat = avg_fiber = 0

        # Get targets for comparison
        targets = await calculate_personalized_targets(user)

        # Calculate adherence percentages
        calorie_adherence = (avg_calories / targets["calories"]) * 100 if targets["calories"] > 0 else 0
        protein_adherence = (avg_protein / targets["protein_g"]) * 100 if targets["protein_g"] > 0 else 0

        # Generate weekly insights
        weekly_insights = []

        if calorie_adherence < 80:
            weekly_insights.append({
                "type": "concern",
                "message": f"Average calorie intake is {round(calorie_adherence)}% of target. Consider adding nutritious snacks.",
                "category": "calories"
            })
        elif calorie_adherence > 120:
            weekly_insights.append({
                "type": "warning",
                "message": f"Average calorie intake is {round(calorie_adherence)}% of target. Focus on portion control.",
                "category": "calories"
            })

        if protein_adherence < 80:
            weekly_insights.append({
                "type": "suggestion",
                "message": f"Protein intake is {round(protein_adherence)}% of target. Include protein in every meal.",
                "category": "protein"
            })

        # Consistency analysis
        calorie_values = [day["calories"] for day in daily_summaries.values()]
        if len(calorie_values) > 1:
            calorie_std = (sum((x - avg_calories) ** 2 for x in calorie_values) / len(calorie_values)) ** 0.5
            consistency_score = max(0, 100 - (calorie_std / avg_calories * 100)) if avg_calories > 0 else 0

            if consistency_score < 70:
                weekly_insights.append({
                    "type": "tip",
                    "message": "Your daily calorie intake varies significantly. Try meal planning for more consistency.",
                    "category": "consistency"
                })
        else:
            consistency_score = 100

        return {
            "period": f"{weeks} week(s)",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days_logged": days_with_data,
            "averages": {
                "calories": round(avg_calories, 1),
                "protein_g": round(avg_protein, 1),
                "carbs_g": round(avg_carbs, 1),
                "fat_g": round(avg_fat, 1),
                "fiber_g": round(avg_fiber, 1)
            },
            "targets": targets,
            "adherence": {
                "calorie_adherence": round(calorie_adherence, 1),
                "protein_adherence": round(protein_adherence, 1),
                "consistency_score": round(consistency_score, 1)
            },
            "daily_breakdown": daily_summaries,
            "insights": weekly_insights,
            "total_foods_logged": sum(day["food_count"] for day in daily_summaries.values())
        }

    except Exception as e:
        print(f"Weekly nutrition summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly nutrition summary: {str(e)}")

# Helper functions for enhanced nutrition calculations
async def calculate_personalized_targets(user):
    """Calculate personalized nutrition targets based on user profile and goals."""
    if not user:
        return {
            "calories": 2000,
            "protein_g": 100,
            "carbs_g": 250,
            "fat_g": 70,
            "fiber_g": 25
        }

    # Get user attributes with defaults
    age = user.get("age", 30)
    gender = user.get("gender", "male")
    weight_kg = user.get("weight_kg", 70)
    height_cm = user.get("height_cm", 170)
    activity_level = user.get("activity_level", "moderately_active")
    primary_goal = user.get("primary_goal", "maintenance")

    # Calculate BMR using Mifflin-St Jeor equation
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Calculate TDEE
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extremely_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    # Adjust calories based on goals
    if primary_goal == "weight_loss":
        target_calories = tdee - 500  # 500 calorie deficit
    elif primary_goal == "weight_gain":
        target_calories = tdee + 500  # 500 calorie surplus
    elif primary_goal == "muscle_gain":
        target_calories = tdee + 300  # Moderate surplus
    else:
        target_calories = tdee  # Maintenance

    # Calculate macronutrient targets based on goals
    if primary_goal == "muscle_gain":
        protein_per_kg = 2.2
        fat_percent = 0.25
    elif primary_goal == "weight_loss":
        protein_per_kg = 2.0
        fat_percent = 0.30
    elif activity_level in ["very_active", "extremely_active"]:
        protein_per_kg = 1.8
        fat_percent = 0.28
    else:
        protein_per_kg = 1.2
        fat_percent = 0.28

    # Calculate targets
    protein_g = weight_kg * protein_per_kg
    fat_g = (target_calories * fat_percent) / 9
    protein_calories = protein_g * 4
    fat_calories = fat_g * 9
    carb_calories = target_calories - protein_calories - fat_calories
    carbs_g = max(0, carb_calories / 4)
    fiber_g = min(35, target_calories / 1000 * 14)  # 14g per 1000 calories

    return {
        "calories": round(target_calories, 1),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1),
        "fiber_g": round(fiber_g, 1),
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1)
    }


async def generate_nutrition_insights(user, actual_intake, targets):
    """Generate personalized nutrition insights based on intake vs targets."""
    insights = []

    # Get user's dietary restrictions, health conditions, and allergies
    dietary_restrictions = user.get("dietary_restrictions", []) if user else []
    health_conditions = user.get("health_conditions", []) if user else []
    allergies = user.get("allergies", []) if user else []

    # Calorie analysis
    calorie_diff = actual_intake["calories"] - targets["calories"]
    if abs(calorie_diff) > 200:
        if calorie_diff > 0:
            insights.append({
                "type": "warning",
                "category": "calories",
                "message": f"You're {round(calorie_diff)} calories over your target. Consider lighter meals or more activity.",
                "priority": "high"
            })
        else:
            insights.append({
                "type": "info",
                "category": "calories",
                "message": f"You're {round(abs(calorie_diff))} calories under your target. Consider adding a healthy snack.",
                "priority": "medium"
            })

    # Protein analysis with dietary restriction considerations
    protein_percent = (actual_intake["protein_g"] / targets["protein_g"]) * 100 if targets["protein_g"] > 0 else 0
    if protein_percent < 80:
        protein_message = f"Protein intake is {round(protein_percent)}% of target."

        # Customize protein recommendations based on dietary restrictions
        if any(restriction.get("type") == "vegan" for restriction in dietary_restrictions):
            protein_message += " Try legumes, quinoa, tofu, tempeh, or plant-based protein powders."
        elif any(restriction.get("type") == "vegetarian" for restriction in dietary_restrictions):
            protein_message += " Include eggs, dairy, legumes, nuts, and seeds."
        elif any(restriction.get("type") == "dairy_free" for restriction in dietary_restrictions):
            protein_message += " Focus on lean meats, fish, eggs, and plant-based proteins."
        else:
            protein_message += " Add lean meats, fish, eggs, or legumes."

        insights.append({
            "type": "warning",
            "category": "protein",
            "message": protein_message,
            "priority": "high"
        })
    elif protein_percent > 150:
        insights.append({
            "type": "info",
            "category": "protein",
            "message": "Protein intake is high. Ensure adequate hydration and kidney health.",
            "priority": "low"
        })

    # Fiber analysis with health condition considerations
    if actual_intake["fiber_g"] < targets["fiber_g"] * 0.7:
        fiber_message = "Increase fiber for better digestion."

        # Customize fiber recommendations based on health conditions
        if any("diabetes" in condition.get("name", "").lower() for condition in health_conditions):
            fiber_message += " High-fiber foods help manage blood sugar levels."
        elif any("heart" in condition.get("name", "").lower() for condition in health_conditions):
            fiber_message += " Soluble fiber can help lower cholesterol."

        # Add safe fiber sources based on restrictions
        if any(restriction.get("type") == "gluten_free" for restriction in dietary_restrictions):
            fiber_message += " Try quinoa, brown rice, fruits, and vegetables."
        else:
            fiber_message += " Include whole grains, fruits, vegetables, and legumes."

        insights.append({
            "type": "suggestion",
            "category": "fiber",
            "message": fiber_message,
            "priority": "medium"
        })

    # Health condition-specific insights
    for condition in health_conditions:
        condition_name = condition.get("name", "").lower()

        if "diabetes" in condition_name:
            insights.append({
                "type": "health_alert",
                "category": "diabetes",
                "message": "Monitor carbohydrate intake and choose low-glycemic foods. Consider pairing carbs with protein.",
                "priority": "high"
            })
        elif "hypertension" in condition_name or "blood pressure" in condition_name:
            insights.append({
                "type": "health_alert",
                "category": "hypertension",
                "message": "Limit sodium intake and include potassium-rich foods like bananas and leafy greens.",
                "priority": "high"
            })
        elif "heart" in condition_name:
            insights.append({
                "type": "health_alert",
                "category": "heart_health",
                "message": "Focus on omega-3 rich foods, limit saturated fats, and include antioxidant-rich foods.",
                "priority": "high"
            })
        elif "anemia" in condition_name:
            insights.append({
                "type": "health_alert",
                "category": "anemia",
                "message": "Include iron-rich foods and pair with vitamin C for better absorption.",
                "priority": "high"
            })

    # Allergy safety reminders
    if allergies:
        # Handle both string and object formats for allergies
        allergy_names = []
        for allergy in allergies:
            if isinstance(allergy, str):
                allergy_names.append(allergy)
            elif isinstance(allergy, dict):
                allergy_names.append(allergy.get('allergy', ''))

        if allergy_names:
            insights.append({
                "type": "safety_alert",
                "category": "allergies",
                "message": f"Remember to avoid: {', '.join(allergy_names)}. Always check food labels carefully.",
                "priority": "high"
            })

    # Goal-specific insights
    primary_goal = user.get("primary_goal", "maintenance") if user else "maintenance"
    if primary_goal == "muscle_gain" and protein_percent < 90:
        insights.append({
            "type": "suggestion",
            "category": "muscle_gain",
            "message": "For muscle gain, prioritize protein intake within 2 hours post-workout.",
            "priority": "high"
        })
    elif primary_goal == "weight_loss" and calorie_diff > 100:
        insights.append({
            "type": "suggestion",
            "category": "weight_loss",
            "message": "Focus on high-volume, low-calorie foods like vegetables to stay satisfied.",
            "priority": "high"
        })

    return insights


# Food safety and filtering functions
def is_food_safe_for_user(food_name, food_description, user):
    """Check if a food is safe for user based on allergies, restrictions, and health conditions."""
    if not user:
        return True, []

    warnings = []
    food_lower = f"{food_name} {food_description}".lower()

    # Check allergies
    allergies = user.get("allergies", [])
    for allergy in allergies:
        # Handle both string and object formats
        allergy_name = allergy if isinstance(allergy, str) else allergy.get('allergy', '') if isinstance(allergy, dict) else ''
        if allergy_name and allergy_name.lower() in food_lower:
            return False, [f"⚠️ ALLERGY ALERT: Contains {allergy_name}"]

    # Check dietary restrictions
    dietary_restrictions = user.get("dietary_restrictions", [])
    for restriction in dietary_restrictions:
        restriction_type = restriction.get("type", "").lower()

        if restriction_type == "vegan":
            non_vegan_items = ["meat", "chicken", "beef", "pork", "fish", "salmon", "tuna", "dairy", "milk", "cheese", "yogurt", "egg", "honey"]
            if any(item in food_lower for item in non_vegan_items):
                return False, [f"🌱 Not suitable for vegan diet"]

        elif restriction_type == "vegetarian":
            non_vegetarian_items = ["meat", "chicken", "beef", "pork", "fish", "salmon", "tuna", "seafood"]
            if any(item in food_lower for item in non_vegetarian_items):
                return False, [f"🥬 Not suitable for vegetarian diet"]

        elif restriction_type == "gluten_free":
            gluten_items = ["wheat", "barley", "rye", "bread", "pasta", "flour", "gluten"]
            if any(item in food_lower for item in gluten_items):
                return False, [f"🌾 Contains gluten"]

        elif restriction_type == "dairy_free":
            dairy_items = ["milk", "cheese", "yogurt", "butter", "cream", "dairy", "lactose"]
            if any(item in food_lower for item in dairy_items):
                return False, [f"🥛 Contains dairy"]

        elif restriction_type == "nut_free":
            nut_items = ["nut", "almond", "walnut", "peanut", "cashew", "pecan", "hazelnut"]
            if any(item in food_lower for item in nut_items):
                return False, [f"🥜 Contains nuts"]

    # Check health condition considerations
    health_conditions = user.get("health_conditions", [])
    for condition in health_conditions:
        condition_name = condition.get("name", "").lower()

        if "diabetes" in condition_name:
            high_sugar_items = ["candy", "soda", "cake", "cookie", "donut", "ice cream", "syrup"]
            if any(item in food_lower for item in high_sugar_items):
                warnings.append("🍬 High sugar content - monitor blood glucose")

        elif "hypertension" in condition_name or "blood pressure" in condition_name:
            high_sodium_items = ["salt", "sodium", "pickle", "processed", "canned", "bacon", "sausage"]
            if any(item in food_lower for item in high_sodium_items):
                warnings.append("🧂 High sodium content - monitor blood pressure")

        elif "heart" in condition_name:
            high_fat_items = ["fried", "butter", "lard", "fatty", "processed meat"]
            if any(item in food_lower for item in high_fat_items):
                warnings.append("❤️ High saturated fat - consider heart-healthy alternatives")

    return True, warnings


def get_safe_food_suggestions(user, nutrient_type, amount_needed):
    """Get food suggestions that are safe for the user's restrictions and conditions."""
    # Base food suggestions by nutrient type
    food_suggestions = {
        "protein": [
            {"name": "Grilled chicken breast (100g)", "protein_g": 31, "calories": 165, "tags": ["meat", "lean"]},
            {"name": "Greek yogurt (1 cup)", "protein_g": 20, "calories": 130, "tags": ["dairy"]},
            {"name": "Lentils (1 cup cooked)", "protein_g": 18, "calories": 230, "tags": ["vegan", "gluten_free"]},
            {"name": "Salmon fillet (100g)", "protein_g": 25, "calories": 208, "tags": ["fish", "omega3"]},
            {"name": "Tofu (100g)", "protein_g": 15, "calories": 144, "tags": ["vegan", "soy"]},
            {"name": "Eggs (2 large)", "protein_g": 12, "calories": 140, "tags": ["vegetarian"]},
            {"name": "Quinoa (1 cup cooked)", "protein_g": 8, "calories": 222, "tags": ["vegan", "gluten_free"]},
            {"name": "Black beans (1 cup)", "protein_g": 15, "calories": 227, "tags": ["vegan", "gluten_free"]},
            {"name": "Almonds (30g)", "protein_g": 6, "calories": 174, "tags": ["vegan", "nuts"]},
            {"name": "Cottage cheese (1 cup)", "protein_g": 28, "calories": 220, "tags": ["dairy", "vegetarian"]}
        ],
        "fiber": [
            {"name": "Apple with skin", "fiber_g": 4.4, "calories": 95, "tags": ["vegan", "gluten_free"]},
            {"name": "Black beans (1/2 cup)", "fiber_g": 7.5, "calories": 114, "tags": ["vegan", "gluten_free"]},
            {"name": "Broccoli (1 cup)", "fiber_g": 5.1, "calories": 55, "tags": ["vegan", "gluten_free"]},
            {"name": "Oatmeal (1 cup)", "fiber_g": 4, "calories": 147, "tags": ["vegan"]},
            {"name": "Avocado (1 medium)", "fiber_g": 10, "calories": 234, "tags": ["vegan", "gluten_free"]},
            {"name": "Raspberries (1 cup)", "fiber_g": 8, "calories": 64, "tags": ["vegan", "gluten_free"]},
            {"name": "Sweet potato (1 medium)", "fiber_g": 3.8, "calories": 112, "tags": ["vegan", "gluten_free"]},
            {"name": "Chia seeds (2 tbsp)", "fiber_g": 10, "calories": 138, "tags": ["vegan", "gluten_free"]}
        ],
        "calories": [
            {"name": "Banana with peanut butter", "calories": 270, "tags": ["vegetarian", "nuts"]},
            {"name": "Trail mix (30g)", "calories": 150, "tags": ["vegetarian", "nuts"]},
            {"name": "Whole grain toast with avocado", "calories": 200, "tags": ["vegan"]},
            {"name": "Smoothie with protein powder", "calories": 300, "tags": ["vegetarian"]},
            {"name": "Granola bar", "calories": 180, "tags": ["vegetarian"]},
            {"name": "Hummus with vegetables", "calories": 120, "tags": ["vegan", "gluten_free"]}
        ]
    }

    # Filter suggestions based on user's restrictions
    safe_suggestions = []
    suggestions = food_suggestions.get(nutrient_type, food_suggestions["calories"])

    for suggestion in suggestions:
        is_safe, warnings = is_food_safe_for_user(suggestion["name"], "", user)
        if is_safe:
            # Add any warnings to the suggestion
            if warnings:
                suggestion["warnings"] = warnings
            safe_suggestions.append(suggestion)

    return safe_suggestions[:5]  # Return top 5 safe suggestions


@app.get("/api/v1/foods/log/daily")
async def get_daily_nutrition(target_date: Optional[str] = None):
    """Get enhanced daily nutrition summary with AI-powered insights."""
    try:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Get food logs for the target date
        daily_logs = await db.food_logs.find({
            "user_id": user_id,
            "date": target_date
        }).to_list(length=None)

        # Calculate totals with safe float conversion
        def safe_float(value):
            try:
                return float(value) if value not in [None, '', 'None'] else 0.0
            except (ValueError, TypeError):
                return 0.0

        total_calories = sum(safe_float(log.get("calories", 0)) for log in daily_logs)
        total_protein = sum(safe_float(log.get("protein_g", 0)) for log in daily_logs)
        total_carbs = sum(safe_float(log.get("carbs_g", 0)) for log in daily_logs)
        total_fat = sum(safe_float(log.get("fat_g", 0)) for log in daily_logs)
        total_fiber = sum(safe_float(log.get("fiber_g", 0)) for log in daily_logs)
        total_sugar = sum(safe_float(log.get("sugar_g", 0)) for log in daily_logs)
        total_sodium = sum(safe_float(log.get("sodium_mg", 0)) for log in daily_logs)

        # Group by meal type with enhanced details
        meals = {}
        for log in daily_logs:
            meal_type = log.get("meal_type", "other")
            if meal_type not in meals:
                meals[meal_type] = {
                    "foods": [],
                    "calories": 0,
                    "protein_g": 0,
                    "carbs_g": 0,
                    "fat_g": 0
                }

            food_item = {
                "id": str(log.get("_id", "")),
                "food_description": log.get("food_description"),
                "quantity": log.get("quantity"),
                "unit": log.get("unit"),
                "calories": safe_float(log.get("calories", 0)),
                "protein_g": safe_float(log.get("protein_g", 0)),
                "carbs_g": safe_float(log.get("carbs_g", 0)),
                "fat_g": safe_float(log.get("fat_g", 0)),
                "notes": log.get("notes", "")
            }
            meals[meal_type]["foods"].append(food_item)
            meals[meal_type]["calories"] += food_item["calories"]
            meals[meal_type]["protein_g"] += food_item["protein_g"]
            meals[meal_type]["carbs_g"] += food_item["carbs_g"]
            meals[meal_type]["fat_g"] += food_item["fat_g"]

        # Calculate personalized targets based on user profile
        targets = await calculate_personalized_targets(user)

        # Calculate progress percentages
        calorie_progress = (total_calories / targets["calories"]) * 100 if targets["calories"] > 0 else 0
        protein_progress = (total_protein / targets["protein_g"]) * 100 if targets["protein_g"] > 0 else 0
        carbs_progress = (total_carbs / targets["carbs_g"]) * 100 if targets["carbs_g"] > 0 else 0
        fat_progress = (total_fat / targets["fat_g"]) * 100 if targets["fat_g"] > 0 else 0

        # Generate insights based on current intake vs targets
        insights = await generate_nutrition_insights(user, {
            "calories": total_calories,
            "protein_g": total_protein,
            "carbs_g": total_carbs,
            "fat_g": total_fat,
            "fiber_g": total_fiber
        }, targets)

        return {
            "date": target_date,
            "summary": {
                "actual_calories": round(total_calories, 1),
                "actual_protein_g": round(total_protein, 1),
                "actual_carbs_g": round(total_carbs, 1),
                "actual_fat_g": round(total_fat, 1),
                "actual_fiber_g": round(total_fiber, 1),
                "actual_sugar_g": round(total_sugar, 1),
                "actual_sodium_mg": round(total_sodium, 1)
            },
            "targets": targets,
            "progress": {
                "calorie_progress": round(calorie_progress, 1),
                "protein_progress": round(protein_progress, 1),
                "carbs_progress": round(carbs_progress, 1),
                "fat_progress": round(fat_progress, 1)
            },
            "remaining": {
                "calories": max(0, targets["calories"] - total_calories),
                "protein_g": max(0, targets["protein_g"] - total_protein),
                "carbs_g": max(0, targets["carbs_g"] - total_carbs),
                "fat_g": max(0, targets["fat_g"] - total_fat)
            },
            "meals": meals,
            "insights": insights,
            "food_count": len(daily_logs)
        }

    except Exception as e:
        print(f"Daily nutrition error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily nutrition: {str(e)}")

@app.get("/api/v1/foods/log/history")
async def get_food_history(days: int = 7):
    """Get food history from MongoDB."""
    try:
        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Get recent food logs
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = await db.food_logs.find({
            "user_id": user_id,
            "logged_at": {"$gte": start_date}
        }).sort("logged_at", -1).limit(50).to_list(length=None)

        return [serialize_doc(log) for log in logs]

    except Exception as e:
        print(f"Food history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get food history")

# AI Chatbot endpoint
@app.post("/api/v1/chat/message")
async def chat_with_ai(request: dict):
    """Chat with AI nutrition assistant using Gemini."""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Get user context for personalized responses
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_profile = serialize_doc(user) if user else {}

        # Get current nutrition data for context
        daily_nutrition = await get_daily_nutrition()

        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                # Create comprehensive context for the AI
                context_prompt = f"""
                You are NourishAI, a friendly and knowledgeable nutrition assistant. You help users with:
                - Nutrition advice and meal planning
                - Food recommendations based on dietary needs
                - Answering questions about healthy eating
                - Providing personalized suggestions

                User Context:
                - Current daily nutrition: {daily_nutrition}
                - User profile: {user_profile}

                Guidelines:
                - Be friendly, helpful, and encouraging
                - Provide evidence-based nutrition advice
                - Ask clarifying questions when needed
                - Suggest specific foods and meals
                - Keep responses concise but informative
                - If asked about medical conditions, recommend consulting healthcare professionals
                - Focus on practical, actionable advice

                User Message: "{message}"

                Respond as NourishAI in a conversational, helpful tone. Provide specific, actionable nutrition advice.
                """

                response = gemini_model.generate_content(context_prompt)
                ai_response = response.text.strip()

                # Store chat history in MongoDB
                chat_entry = {
                    "user_id": str(user["_id"]) if user else "demo_user",
                    "user_message": message,
                    "ai_response": ai_response,
                    "timestamp": datetime.utcnow(),
                    "context": {
                        "daily_nutrition": daily_nutrition,
                        "user_profile_summary": {
                            "dietary_restrictions": user_profile.get("dietary_restrictions", []) if user_profile else [],
                            "health_conditions": user_profile.get("health_conditions", []) if user_profile else [],
                            "allergies": user_profile.get("allergies", []) if user_profile else []
                        }
                    }
                }

                await db.chat_history.insert_one(chat_entry)

                return {
                    "response": ai_response,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": True
                }

            except Exception as e:
                print(f"❌ Gemini chat error: {e}")
                return {
                    "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": False,
                    "error": "AI service temporarily unavailable"
                }
        else:
            # Fallback response when Gemini is not available
            return {
                "response": "Hello! I'm NourishAI, your nutrition assistant. I'm currently in limited mode. I can help you with basic nutrition questions, but for the best experience, please ensure the AI service is properly configured.",
                "timestamp": datetime.utcnow().isoformat(),
                "context_used": False,
                "error": "AI service not available"
            }

    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@app.get("/api/v1/chat/history")
async def get_chat_history(limit: int = 20):
    """Get recent chat history."""
    try:
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user"

        chat_history = await db.chat_history.find(
            {"user_id": user_id},
            {"_id": 0, "user_message": 1, "ai_response": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(limit).to_list(length=limit)

        # Reverse to get chronological order
        chat_history.reverse()

        return {
            "chat_history": chat_history,
            "total_messages": len(chat_history)
        }

    except Exception as e:
        print(f"❌ Chat history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

# MongoDB-backed Recommendations with Gemini AI
@app.post("/api/v1/recommendations/generate")
async def generate_recommendations():
    """Generate and store AI-powered recommendations in MongoDB."""
    try:
        # Get current user and their nutrition data
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Get today's nutrition data
        daily_nutrition = await get_daily_nutrition()

        recommendations = []

        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                # Create comprehensive prompt for Gemini
                user_profile = serialize_doc(user) if user else {}

                prompt = f"""
                You are a professional nutritionist AI. Generate 3 personalized nutrition recommendations for this user:

                User Profile:
                - Age: {user_profile.get('age', 'unknown')}
                - Gender: {user_profile.get('gender', 'unknown')}
                - Weight: {user_profile.get('weight_kg', 'unknown')}kg
                - Height: {user_profile.get('height_cm', 'unknown')}cm
                - Activity Level: {user_profile.get('activity_level', 'unknown')}
                - Primary Goal: {user_profile.get('primary_goal', 'unknown')}
                - Health Conditions: {user_profile.get('health_conditions', [])}
                - Dietary Restrictions: {user_profile.get('dietary_restrictions', [])}
                - Allergies: {user_profile.get('allergies', [])}

                Current Daily Intake:
                - Calories: {daily_nutrition.get('actual_calories', 0)} / {daily_nutrition.get('target_calories', 2000)}
                - Protein: {daily_nutrition.get('actual_protein_g', 0)}g / {daily_nutrition.get('target_protein_g', 100)}g
                - Carbs: {daily_nutrition.get('actual_carbs_g', 0)}g / {daily_nutrition.get('target_carbs_g', 250)}g
                - Fat: {daily_nutrition.get('actual_fat_g', 0)}g / {daily_nutrition.get('target_fat_g', 70)}g

                Generate evidence-based recommendations focusing on:
                1. Nutrient gaps or excesses with specific food recommendations
                2. Foods that address multiple nutrient needs simultaneously
                3. Health condition considerations and safe food choices
                4. Dietary restriction and allergy-compliant suggestions
                5. Practical implementation advice with meal timing
                6. Budget-friendly and accessible food options

                Return as JSON array:
                [
                    {{
                        "recommendation_type": "NUTRIENT_ADJUSTMENT|FOOD_SUGGESTION|MEAL_PLAN",
                        "title": "Clear, actionable title",
                        "description": "Detailed explanation with scientific reasoning",
                        "confidence_level": "high|medium|low",
                        "priority": 1-3,
                        "expected_impact": "high|medium|low",
                        "implementation_difficulty": "easy|medium|hard",
                        "time_horizon": "short_term|medium_term|long_term",
                        "nutrient_adjustments": [
                            {{
                                "nutrient_name": "protein_g",
                                "current_intake": number,
                                "recommended_intake": number,
                                "adjustment_amount": number,
                                "adjustment_direction": "increase|decrease",
                                "unit": "g|mg|mcg",
                                "reason": "specific reason for adjustment",
                                "food_sources": ["food1", "food2", "food3"],
                                "health_impact": "explanation of health benefits"
                            }}
                        ],
                        "food_suggestions": [
                            {{
                                "food_name": "Specific food name",
                                "serving_size": number,
                                "serving_unit": "cup|oz|gram|piece",
                                "calories": number,
                                "key_nutrients": {{
                                    "protein_g": number,
                                    "fiber_g": number,
                                    "iron_mg": number,
                                    "vitamin_c_mg": number
                                }},
                                "reason": "Why this food addresses the nutrient gap",
                                "nutritional_benefits": ["benefit1", "benefit2"],
                                "preparation_tips": "How to prepare or consume",
                                "meal_timing": "breakfast|lunch|dinner|snack|pre_workout|post_workout",
                                "cost_effectiveness": "low|medium|high",
                                "availability": "common|seasonal|specialty"
                            }}
                        ],
                        "meal_combinations": [
                            {{
                                "combination_name": "Nutrient-dense meal idea",
                                "foods": ["food1", "food2", "food3"],
                                "total_nutrients": {{"protein_g": number, "calories": number}},
                                "preparation_time": "5-10 minutes",
                                "meal_type": "breakfast|lunch|dinner|snack"
                            }}
                        ]
                    }}
                ]

                Focus on practical, evidence-based recommendations. Respond with valid JSON only.
                """

                response = gemini_model.generate_content(prompt)
                content = response.text.strip()

                # Clean up response
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()

                ai_recommendations = json.loads(content)

                # Store each recommendation in MongoDB
                for i, rec in enumerate(ai_recommendations):
                    rec_doc = {
                        "user_id": user_id,
                        "recommendation_id": f"rec_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                        "recommendation_type": rec.get("recommendation_type", "GENERAL"),
                        "title": rec.get("title", "Nutrition Recommendation"),
                        "description": rec.get("description", ""),
                        "confidence_level": rec.get("confidence_level", "medium"),
                        "priority": rec.get("priority", 2),
                        "expected_impact": rec.get("expected_impact", "medium"),
                        "implementation_difficulty": rec.get("implementation_difficulty", "medium"),
                        "time_horizon": rec.get("time_horizon", "short_term"),
                        "nutrient_adjustments": rec.get("nutrient_adjustments", []),
                        "food_suggestions": rec.get("food_suggestions", []),
                        "is_active": True,
                        "is_viewed": False,
                        "is_accepted": None,
                        "user_rating": None,
                        "created_at": datetime.utcnow(),
                        "source": "gemini_ai"
                    }

                    # Insert recommendation into database
                    result = await db.recommendations.insert_one(rec_doc)
                    rec_doc["_id"] = result.inserted_id
                    rec_doc["id"] = rec_doc["recommendation_id"]

                    recommendations.append(serialize_doc(rec_doc))

                print(f"✅ Generated and stored {len(recommendations)} AI recommendations")
                return recommendations

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse Gemini JSON: {e}")
            except Exception as e:
                print(f"❌ Gemini recommendation error: {e}")

        # Fallback: Generate rule-based recommendations
        print("🔄 Generating fallback recommendations...")

        # Analyze nutrition gaps and create recommendations
        calorie_gap = daily_nutrition.get('target_calories', 2000) - daily_nutrition.get('actual_calories', 0)
        protein_gap = daily_nutrition.get('target_protein_g', 100) - daily_nutrition.get('actual_protein_g', 0)

        fallback_recommendations = []

        if abs(calorie_gap) > 200:
            rec_doc = {
                "user_id": user_id,
                "recommendation_id": f"rec_calories_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "recommendation_type": "NUTRIENT_ADJUSTMENT",
                "title": f"{'Increase' if calorie_gap > 0 else 'Reduce'} Daily Calorie Intake",
                "description": f"Your current calorie intake is {'below' if calorie_gap > 0 else 'above'} your target by {abs(calorie_gap):.0f} calories.",
                "confidence_level": "high",
                "priority": 1 if abs(calorie_gap) > 500 else 2,
                "expected_impact": "high",
                "implementation_difficulty": "medium",
                "time_horizon": "short_term",
                "nutrient_adjustments": [{
                    "nutrient_name": "calories",
                    "current_intake": daily_nutrition.get('actual_calories', 0),
                    "recommended_intake": daily_nutrition.get('target_calories', 2000),
                    "adjustment_amount": abs(calorie_gap),
                    "adjustment_direction": "increase" if calorie_gap > 0 else "decrease",
                    "unit": "kcal",
                    "reason": f"Current intake is {'insufficient' if calorie_gap > 0 else 'excessive'} for your goals",
                    "food_sources": ["lean proteins", "whole grains", "healthy fats"] if calorie_gap > 0 else ["vegetables", "lean proteins"]
                }],
                "is_active": True,
                "is_viewed": False,
                "is_accepted": None,
                "user_rating": None,
                "created_at": datetime.utcnow(),
                "source": "rule_based"
            }

            result = await db.recommendations.insert_one(rec_doc)
            rec_doc["_id"] = result.inserted_id
            rec_doc["id"] = rec_doc["recommendation_id"]
            fallback_recommendations.append(serialize_doc(rec_doc))

        if protein_gap > 20:
            rec_doc = {
                "user_id": user_id,
                "recommendation_id": f"rec_protein_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "recommendation_type": "NUTRIENT_ADJUSTMENT",
                "title": "Increase Protein Intake",
                "description": f"You're consuming {protein_gap:.0f}g less protein than recommended. Adequate protein supports muscle maintenance and satiety.",
                "confidence_level": "high",
                "priority": 2,
                "expected_impact": "high",
                "implementation_difficulty": "easy",
                "time_horizon": "short_term",
                "nutrient_adjustments": [{
                    "nutrient_name": "protein_g",
                    "current_intake": daily_nutrition.get('actual_protein_g', 0),
                    "recommended_intake": daily_nutrition.get('target_protein_g', 100),
                    "adjustment_amount": protein_gap,
                    "adjustment_direction": "increase",
                    "unit": "g",
                    "reason": "Current intake is below recommended daily value",
                    "food_sources": ["chicken breast", "fish", "eggs", "legumes", "Greek yogurt"]
                }],
                "is_active": True,
                "is_viewed": False,
                "is_accepted": None,
                "user_rating": None,
                "created_at": datetime.utcnow(),
                "source": "rule_based"
            }

            result = await db.recommendations.insert_one(rec_doc)
            rec_doc["_id"] = result.inserted_id
            rec_doc["id"] = rec_doc["recommendation_id"]
            fallback_recommendations.append(serialize_doc(rec_doc))

        return fallback_recommendations if fallback_recommendations else recommendations

    except Exception as e:
        print(f"Recommendation generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@app.get("/api/v1/recommendations/")
async def get_recommendations(active_only: bool = True, limit: int = 10):
    """Get user's recommendations from MongoDB."""
    try:
        # Get current user
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_id = str(user["_id"]) if user else "demo_user_id"

        # Build query
        query = {"user_id": user_id}
        if active_only:
            query["is_active"] = True

        # Get recommendations from database
        recommendations = await db.recommendations.find(query).sort("created_at", -1).limit(limit).to_list(length=None)

        return [serialize_doc(rec) for rec in recommendations]

    except Exception as e:
        print(f"Get recommendations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@app.get("/api/v1/recommendations/{recommendation_id}")
async def get_recommendation_details(recommendation_id: str):
    """Get detailed recommendation from MongoDB."""
    try:
        recommendation = await db.recommendations.find_one({"recommendation_id": recommendation_id})

        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Mark as viewed
        await db.recommendations.update_one(
            {"_id": recommendation["_id"]},
            {"$set": {"is_viewed": True}}
        )

        return serialize_doc(recommendation)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Get recommendation details error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation details")

@app.post("/api/v1/recommendations/{recommendation_id}/feedback")
async def submit_recommendation_feedback(recommendation_id: str, feedback: dict):
    """Submit feedback for a recommendation in MongoDB."""
    try:
        # Update recommendation with feedback
        update_data = {
            "is_accepted": feedback.get("is_accepted"),
            "user_rating": feedback.get("rating"),
            "user_feedback": feedback.get("feedback", ""),
            "feedback_at": datetime.utcnow()
        }

        result = await db.recommendations.update_one(
            {"recommendation_id": recommendation_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        print(f"✅ Feedback submitted for {recommendation_id}: {feedback}")
        return {
            "message": "Feedback submitted successfully",
            "recommendation_id": recommendation_id,
            "feedback": feedback
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Submit feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")



@app.get("/api/v1/meal-plans")
async def get_meal_plan_recommendations(
    target_calories: Optional[int] = None,
    meal_count: int = 3,
    days: int = 1
):
    """Generate complete meal plans based on user's nutritional needs."""
    try:
        # Get current user and nutrition data
        user = await db.users.find_one({}, sort=[("created_at", -1)])
        user_profile = serialize_doc(user) if user else {}
        daily_nutrition = await get_daily_nutrition()

        # Use target calories from user profile or parameter
        if not target_calories:
            target_calories = user_profile.get('target_calories') or daily_nutrition.get('target_calories', 2000)

        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                prompt = f"""
                Create a {days}-day meal plan for a user with these requirements:

                User Profile:
                - Age: {user_profile.get('age', 'unknown')}
                - Gender: {user_profile.get('gender', 'unknown')}
                - Weight: {user_profile.get('weight_kg', 'unknown')}kg
                - Activity Level: {user_profile.get('activity_level', 'unknown')}
                - Primary Goal: {user_profile.get('primary_goal', 'unknown')}
                - Dietary Restrictions: {[dr.get('type', '') for dr in user_profile.get('dietary_restrictions', [])]}
                - Allergies: {user_profile.get('allergies', [])}

                Target Daily Calories: {target_calories}
                Meals per Day: {meal_count}

                Create balanced meal plans that:
                1. Meet the calorie target (±100 calories)
                2. Provide balanced macronutrients (20% protein, 50% carbs, 30% fat)
                3. Include variety and nutrient density
                4. Respect dietary restrictions and allergies
                5. Are practical and affordable

                Return as JSON:
                {{
                    "meal_plan": {{
                        "total_days": {days},
                        "daily_target_calories": {target_calories},
                        "days": [
                            {{
                                "day": 1,
                                "date": "2024-01-15",
                                "total_calories": number,
                                "total_protein_g": number,
                                "total_carbs_g": number,
                                "total_fat_g": number,
                                "meals": {{
                                    "breakfast": {{
                                        "meal_name": "Nutritious breakfast name",
                                        "calories": number,
                                        "foods": [
                                            {{
                                                "food_name": "food item",
                                                "serving_size": number,
                                                "serving_unit": "unit",
                                                "calories": number,
                                                "protein_g": number,
                                                "carbs_g": number,
                                                "fat_g": number
                                            }}
                                        ],
                                        "preparation_time": "15 minutes",
                                        "instructions": "Brief preparation steps"
                                    }},
                                    "lunch": {{"similar structure"}},
                                    "dinner": {{"similar structure"}}
                                }}
                            }}
                        ]
                    }},
                    "shopping_list": {{
                        "produce": ["item1", "item2"],
                        "proteins": ["item1", "item2"],
                        "grains": ["item1", "item2"],
                        "dairy": ["item1", "item2"],
                        "pantry": ["item1", "item2"]
                    }},
                    "nutrition_summary": {{
                        "avg_daily_calories": number,
                        "avg_daily_protein_g": number,
                        "avg_daily_carbs_g": number,
                        "avg_daily_fat_g": number,
                        "key_nutrients_covered": ["nutrient1", "nutrient2"]
                    }}
                }}

                Focus on whole foods and balanced nutrition. Respond with valid JSON only.
                """

                response = gemini_model.generate_content(prompt)
                content = response.text.strip()

                # Clean up response
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()

                meal_plan = json.loads(content)

                print(f"✅ Generated {days}-day meal plan with Gemini AI")
                return meal_plan

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse Gemini meal plan JSON: {e}")
            except Exception as e:
                print(f"❌ Gemini meal plan error: {e}")

        # Fallback: Simple meal plan
        return {
            "meal_plan": {
                "total_days": days,
                "daily_target_calories": target_calories,
                "message": "AI meal planning temporarily unavailable. Please try the food recommendations endpoint for specific food suggestions."
            },
            "source": "fallback"
        }

    except Exception as e:
        print(f"Meal plan error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

if __name__ == "__main__":
    print("🚀 Starting MongoDB Production Nutrient Recommendation System...")
    print("📊 Real Data Sources:")
    print(f"   ✅ USDA FoodData Central API")
    print(f"   {'✅' if GEMINI_AVAILABLE else '❌'} Google Gemini AI")
    print(f"   ✅ MongoDB Atlas (Persistent Storage)")
    print("📖 API Documentation: http://localhost:8002/docs")

    # Get port from environment (Render sets PORT automatically)
    port = int(os.getenv("PORT", 8002))

    uvicorn.run(
        "mongodb_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
