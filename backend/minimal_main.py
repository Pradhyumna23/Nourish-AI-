"""
Ultra-minimal NourishAI backend for Render deployment
Avoiding all compilation issues by using minimal dependencies
"""

import os
import json
import ssl
import uvicorn
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pymongo
from pymongo import MongoClient
from passlib.context import CryptContext
from jose import jwt, JWTError
import requests

# Environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nutrient_db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database connection
client = None
db = None

# FastAPI app
app = FastAPI(
    title="NourishAI - Minimal Render Deployment",
    description="Ultra-minimal version for reliable Render deployment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
@app.on_event("startup")
async def startup_db_client():
    global client, db
    try:
        # Parse the MongoDB URL to add SSL parameters
        if "mongodb+srv://" in MONGODB_URL:
            # For MongoDB Atlas, use specific SSL configuration for Render
            connection_params = {
                "serverSelectionTimeoutMS": 10000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000,
                "maxPoolSize": 10,
                "retryWrites": True,
                "w": "majority",
                # SSL/TLS configuration for Render compatibility
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "tlsAllowInvalidHostnames": True,
                "ssl_cert_reqs": "CERT_NONE"
            }

            # Create connection string with SSL parameters
            if "?" in MONGODB_URL:
                base_url = MONGODB_URL.split("?")[0]
                ssl_params = "&".join([
                    "ssl=true",
                    "ssl_cert_reqs=CERT_NONE",
                    "tlsAllowInvalidCertificates=true",
                    "retryWrites=true",
                    "w=majority"
                ])
                mongodb_url = f"{base_url}?{ssl_params}"
            else:
                ssl_params = "?ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"
                mongodb_url = f"{MONGODB_URL}{ssl_params}"
        else:
            mongodb_url = MONGODB_URL
            connection_params = {
                "serverSelectionTimeoutMS": 10000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000,
            }

        print(f"🔗 Attempting MongoDB connection...")
        client = MongoClient(mongodb_url, **connection_params)
        db = client.nutrient_db

        # Test connection with timeout
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")

    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("🔄 Trying alternative connection method...")

        # Try alternative connection without SSL verification
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Extract base URL without parameters
            base_url = MONGODB_URL.split("?")[0] if "?" in MONGODB_URL else MONGODB_URL

            client = MongoClient(
                base_url,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                socketTimeoutMS=15000,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                ssl_match_hostname=False,
                retryWrites=True,
                w="majority"
            )
            db = client.nutrient_db
            client.admin.command('ping')
            print("✅ Connected to MongoDB with alternative method")

        except Exception as e2:
            print(f"❌ Alternative connection also failed: {e2}")
            print("❌ Unable to connect to MongoDB. Application will run without database.")
            client = None
            db = None

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

def get_current_user_from_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if database is available and user exists
        if not db:
            raise HTTPException(status_code=503, detail="Database connection required")

        user = db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "NourishAI - Minimal Render Deployment",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "database": "✅ MongoDB" if db is not None else "❌ Not connected",
            "gemini_ai": "✅ Available" if GEMINI_API_KEY else "❌ Not configured",
            "usda_api": "✅ Available"
        }
    }

@app.get("/health")
async def health_check():
    db_status = "✅ Connected"
    try:
        if client:
            client.admin.command('ping')
    except:
        db_status = "❌ Disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "gemini_available": bool(GEMINI_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/register")
async def register(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        if not all([username, email, password]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if not db:
            raise HTTPException(status_code=503, detail="Database connection required for registration")
        
        # Check if user exists
        if db.users.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        hashed_password = get_password_hash(password)
        user_doc = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        db.users.insert_one(user_doc)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/token")
async def login(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        
        if not all([email, password]):
            raise HTTPException(status_code=400, detail="Missing email or password")
        
        if not db:
            raise HTTPException(status_code=503, detail="Database connection required for login")
        
        # Authenticate user
        user = db.users.find_one({"email": email})
        if not user or not verify_password(password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        if "Incorrect email or password" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

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
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            foods = []
            for food in data.get("foods", []):
                foods.append({
                    "fdc_id": food.get("fdcId"),
                    "description": food.get("description"),
                    "brand_owner": food.get("brandOwner"),
                    "ingredients": food.get("ingredients"),
                    "food_nutrients": food.get("foodNutrients", [])[:10]
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
async def chat_with_ai(request: Request, authorization: str = Header(None)):
    """Simple chat endpoint"""
    user = get_current_user_from_token(authorization)
    
    try:
        data = await request.json()
        message = data.get("message", "")
        
        if not GEMINI_API_KEY:
            return {
                "response": "I'm sorry, but the AI assistant is currently not available. Please try again later.",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Simple Gemini API call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are NourishAI, a helpful nutrition assistant. Provide personalized, accurate nutrition advice. Keep responses concise and actionable.\n\nUser question: {message}"
                }]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "I'm having trouble processing your request.")
        else:
            ai_response = "I'm having trouble processing your request right now. Please try again later."
        
        return {
            "response": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Chat error: {e}")
        return {
            "response": "I'm having trouble processing your request right now. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v1/nutrition/recommendations")
async def get_recommendations(authorization: str = Header(None)):
    """Get basic nutrition recommendations"""
    user = get_current_user_from_token(authorization)
    
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
    
    print("🚀 Starting NourishAI Minimal Deployment...")
    print(f"🌐 Port: {port}")
    print(f"🔑 Gemini AI: {'✅ Available' if GEMINI_API_KEY else '❌ Not configured'}")
    print(f"🗄️ Database: {MONGODB_URL}")
    
    uvicorn.run(
        "minimal_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
