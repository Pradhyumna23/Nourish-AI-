"""
Recommendation models and schemas.
"""

from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    DAILY_NUTRITION = "daily_nutrition"
    FOOD_SUGGESTION = "food_suggestion"
    MEAL_PLAN = "meal_plan"
    NUTRIENT_ADJUSTMENT = "nutrient_adjustment"
    HEALTH_OPTIMIZATION = "health_optimization"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FoodSuggestion(BaseModel):
    """Individual food suggestion."""
    fdc_id: int
    food_name: str
    brand_name: Optional[str] = None
    serving_size: float
    serving_unit: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    
    # Recommendation context
    reason: str
    meal_type: Optional[str] = None
    priority_score: float = Field(..., ge=0, le=1)
    nutritional_benefits: List[str] = []
    
    # User context
    matches_dietary_restrictions: bool = True
    allergen_warnings: List[str] = []


class MealPlan(BaseModel):
    """Meal plan recommendation."""
    date: datetime
    meals: Dict[str, List[FoodSuggestion]]  # breakfast, lunch, dinner, snack
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    
    # Plan metadata
    plan_type: str  # daily, weekly
    difficulty_level: str  # easy, medium, hard
    prep_time_minutes: Optional[int] = None
    cost_estimate: Optional[float] = None


class NutrientAdjustment(BaseModel):
    """Nutrient adjustment recommendation."""
    nutrient_name: str
    current_intake: float
    recommended_intake: float
    adjustment_amount: float
    adjustment_direction: str  # increase, decrease, maintain
    unit: str
    
    # Context
    reason: str
    health_impact: str
    food_sources: List[str] = []
    supplement_suggestion: Optional[str] = None


class Recommendation(Document):
    """AI-generated recommendation document."""
    
    user_id: str
    recommendation_type: RecommendationType
    
    # Core recommendation data
    title: str
    description: str
    confidence_level: ConfidenceLevel
    
    # Type-specific data
    food_suggestions: List[FoodSuggestion] = []
    meal_plan: Optional[MealPlan] = None
    nutrient_adjustments: List[NutrientAdjustment] = []
    
    # ML model information
    model_version: str
    model_confidence: float = Field(..., ge=0, le=1)
    features_used: List[str] = []
    
    # Personalization context
    user_goals: List[str] = []
    health_conditions: List[str] = []
    dietary_restrictions: List[str] = []
    current_nutrition_status: Dict[str, Any] = {}
    
    # Recommendation metadata
    priority: int = Field(..., ge=1, le=5)  # 1 = highest priority
    expected_impact: str  # high, medium, low
    implementation_difficulty: str  # easy, medium, hard
    time_horizon: str  # immediate, short_term, long_term
    
    # Tracking
    is_active: bool = True
    is_viewed: bool = False
    is_accepted: bool = False
    user_feedback: Optional[str] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Expiration and validity
    valid_until: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # System fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "recommendations"
        indexes = [
            "user_id",
            "recommendation_type",
            "created_at",
            ["user_id", "created_at"],
            ["user_id", "is_active"],
            "priority"
        ]


# Pydantic schemas for API
class RecommendationRequest(BaseModel):
    """Schema for requesting recommendations."""
    recommendation_types: Optional[List[RecommendationType]] = None
    include_meal_plan: bool = False
    meal_plan_days: Optional[int] = Field(1, ge=1, le=7)
    max_suggestions: Optional[int] = Field(10, ge=1, le=50)
    dietary_preferences: Optional[List[str]] = []
    exclude_foods: Optional[List[int]] = []  # FDC IDs to exclude


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    confidence_level: ConfidenceLevel
    food_suggestions: List[FoodSuggestion] = []
    meal_plan: Optional[MealPlan] = None
    nutrient_adjustments: List[NutrientAdjustment] = []
    priority: int
    expected_impact: str
    implementation_difficulty: str
    time_horizon: str
    is_viewed: bool
    is_accepted: bool
    user_rating: Optional[int] = None
    created_at: datetime
    valid_until: Optional[datetime] = None


class RecommendationFeedback(BaseModel):
    """Schema for recommendation feedback."""
    recommendation_id: str
    is_accepted: bool
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    implemented_suggestions: Optional[List[int]] = []  # Indices of implemented suggestions


class RecommendationStats(BaseModel):
    """Schema for recommendation statistics."""
    total_recommendations: int
    active_recommendations: int
    accepted_recommendations: int
    average_rating: Optional[float] = None
    recommendations_by_type: Dict[str, int]
    recent_recommendations: List[RecommendationResponse]
