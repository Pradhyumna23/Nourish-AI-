"""
Food and nutrition models.
"""

from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class NutrientInfo(BaseModel):
    """Nutrient information model."""
    nutrient_id: int
    name: str
    unit: str
    amount: float
    derivation_code: Optional[str] = None
    derivation_description: Optional[str] = None


class FoodPortion(BaseModel):
    """Food portion model."""
    id: int
    amount: float
    unit: str
    modifier: Optional[str] = None
    gram_weight: float
    sequence_number: Optional[int] = None


class Food(Document):
    """Food document model from USDA database."""
    
    # USDA identifiers
    fdc_id: int = Field(..., unique=True)
    data_type: str
    description: str
    food_code: Optional[str] = None
    
    # Publication and source info
    publication_date: Optional[datetime] = None
    brand_owner: Optional[str] = None
    brand_name: Optional[str] = None
    subbrand_name: Optional[str] = None
    gtin_upc: Optional[str] = None
    
    # Nutritional information
    nutrients: List[NutrientInfo] = []
    food_portions: List[FoodPortion] = []
    
    # Categories and classification
    food_category: Optional[str] = None
    food_category_id: Optional[int] = None
    wweia_category_code: Optional[int] = None
    wweia_category_description: Optional[str] = None
    
    # Additional metadata
    ingredients: Optional[str] = None
    serving_size: Optional[float] = None
    serving_size_unit: Optional[str] = None
    household_serving_fulltext: Optional[str] = None
    
    # System fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "foods"
        indexes = [
            "fdc_id",
            [("description", "text")],
            "food_category",
            "brand_owner"
        ]


class FoodItem(Document):
    """User's food consumption record."""
    
    user_id: str
    food_id: str  # Reference to Food document
    fdc_id: int  # USDA Food Data Central ID
    
    # Consumption details
    date: datetime
    meal_type: str  # breakfast, lunch, dinner, snack
    quantity: float
    unit: str
    gram_weight: float
    
    # Calculated nutrition (for this serving)
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    # Additional nutrients
    nutrients: Dict[str, float] = {}
    
    # Metadata
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "food_items"
        indexes = [
            "user_id",
            "date",
            ["user_id", "date"],
            "fdc_id"
        ]


# Pydantic schemas for API
class FoodSearch(BaseModel):
    """Schema for food search."""
    query: str = Field(..., min_length=2, max_length=100)
    page_size: Optional[int] = Field(20, ge=1, le=100)
    page_number: Optional[int] = Field(1, ge=1)
    data_type: Optional[List[str]] = None
    sort_by: Optional[str] = "relevance"


class FoodResponse(BaseModel):
    """Schema for food response."""
    fdc_id: int
    description: str
    data_type: str
    brand_owner: Optional[str] = None
    brand_name: Optional[str] = None
    food_category: Optional[str] = None
    nutrients: List[NutrientInfo] = []
    food_portions: List[FoodPortion] = []


class FoodItemCreate(BaseModel):
    """Schema for creating food item."""
    fdc_id: int
    date: datetime
    meal_type: str = Field(..., regex="^(breakfast|lunch|dinner|snack)$")
    quantity: float = Field(..., gt=0)
    unit: str
    notes: Optional[str] = None


class FoodItemResponse(BaseModel):
    """Schema for food item response."""
    id: str
    user_id: str
    fdc_id: int
    food_description: str
    date: datetime
    meal_type: str
    quantity: float
    unit: str
    gram_weight: float
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime


class NutritionSummary(BaseModel):
    """Schema for daily nutrition summary."""
    date: datetime
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sugar_g: float
    total_sodium_mg: float
    meal_breakdown: Dict[str, Dict[str, float]]
    food_items_count: int
