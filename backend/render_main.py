"""
Render-optimized version of NourishAI backend
Minimal dependencies for successful deployment
"""

import os
import uvicorn
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
import google.generativeai as genai

# Environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nutrient_db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize Gemini AI
GEMINI_AVAILABLE = False
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        print("✅ Gemini AI configured successfully")
    except Exception as e:
        print(f"❌ Gemini AI configuration failed: {e}")

# Database connection
client = None
db = None

# FastAPI app
app = FastAPI(
    title="NourishAI - Render Deployment",
    description="AI-powered nutrition assistant optimized for Render",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Data models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessage(BaseModel):
    message: str

# Database connection
@app.on_event("startup")
async def startup_db_client():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.nutrient_db
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        # Continue without database for basic functionality

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if db:
        user = await db.users.find_one({"email": email})
        if user is None:
            raise credentials_exception
        return user
    else:
        # Return mock user if no database
        return {"email": email, "username": "demo_user"}

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "NourishAI - Render Deployment",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "database": "✅ MongoDB Atlas" if db else "❌ Not connected",
            "gemini_ai": "✅ Available" if GEMINI_AVAILABLE else "❌ Not configured",
            "usda_api": "✅ Available"
        }
    }

@app.get("/health")
async def health_check():
    db_status = "✅ Connected"
    try:
        if client:
            await client.admin.command('ping')
    except:
        db_status = "❌ Disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "gemini_available": GEMINI_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/register", response_model=Token)
async def register(user: UserCreate):
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/auth/token", response_model=Token)
async def login(user: UserLogin):
    if not db:
        # Demo mode - allow any login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    # Authenticate user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/foods/search")
async def search_foods(query: str, limit: int = 10):
    """Search foods using USDA API"""
    try:
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": query,
            "pageSize": limit,
            "api_key": USDA_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
        if response.status_code == 200:
            data = response.json()
            foods = []
            for food in data.get("foods", []):
                foods.append({
                    "fdc_id": food.get("fdcId"),
                    "description": food.get("description"),
                    "brand_owner": food.get("brandOwner"),
                    "ingredients": food.get("ingredients"),
                    "food_nutrients": food.get("foodNutrients", [])[:10]  # Limit nutrients
                })
            return {"foods": foods}
        else:
            return {"foods": []}
            
    except Exception as e:
        print(f"USDA API error: {e}")
        # Return mock data if API fails
        return {
            "foods": [
                {
                    "fdc_id": 123456,
                    "description": f"Mock food result for '{query}'",
                    "brand_owner": "Demo Brand",
                    "ingredients": "Demo ingredients",
                    "food_nutrients": [
                        {"nutrientName": "Energy", "value": 200, "unitName": "kcal"},
                        {"nutrientName": "Protein", "value": 10, "unitName": "g"}
                    ]
                }
            ]
        }

@app.post("/api/v1/chat/message")
async def chat_with_ai(message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Chat with Gemini AI for nutrition advice"""
    if not GEMINI_AVAILABLE:
        return {
            "response": "I'm sorry, but the AI assistant is currently not available. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""You are NourishAI, a helpful nutrition assistant. 
        Provide personalized, accurate nutrition advice based on the user's question.
        Keep responses concise and actionable.
        
        User question: {message.message}"""
        
        response = model.generate_content(prompt)
        
        return {
            "response": response.text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Gemini AI error: {e}")
        return {
            "response": "I'm having trouble processing your request right now. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v1/nutrition/recommendations")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Get basic nutrition recommendations"""
    return {
        "recommendations": [
            {
                "title": "Stay Hydrated",
                "description": "Drink at least 8 glasses of water daily",
                "category": "hydration"
            },
            {
                "title": "Eat More Vegetables",
                "description": "Include 5-7 servings of vegetables in your daily diet",
                "category": "nutrition"
            },
            {
                "title": "Balanced Meals",
                "description": "Include protein, carbs, and healthy fats in each meal",
                "category": "balance"
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    # Get port from environment (Render sets PORT automatically)
    port = int(os.getenv("PORT", 8002))
    
    print("🚀 Starting NourishAI Render Deployment...")
    print(f"🌐 Port: {port}")
    print(f"🔑 Gemini AI: {'✅ Available' if GEMINI_AVAILABLE else '❌ Not configured'}")
    print(f"🗄️ Database: {MONGODB_URL}")
    
    uvicorn.run(
        "render_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
