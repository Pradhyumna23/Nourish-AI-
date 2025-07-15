"""
Nutrition profile and daily intake models.
"""

from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class MacroTargets(BaseModel):
    """Macronutrient targets."""
    calories: float = Field(..., gt=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)
    fiber_g: float = Field(..., ge=0)
    
    # Percentages (should add up to 100 for macros)
    protein_percent: Optional[float] = Field(None, ge=0, le=100)
    carbs_percent: Optional[float] = Field(None, ge=0, le=100)
    fat_percent: Optional[float] = Field(None, ge=0, le=100)


class MicronutrientTargets(BaseModel):
    """Micronutrient targets."""
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    vitamin_e_mg: Optional[float] = None
    vitamin_k_mcg: Optional[float] = None
    thiamin_mg: Optional[float] = None
    riboflavin_mg: Optional[float] = None
    niacin_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    folate_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None


class NutritionProfile(Document):
    """User's nutrition profile and targets."""
    
    user_id: str = Field(..., unique=True)
    
    # Calculated targets
    macro_targets: MacroTargets
    micronutrient_targets: MicronutrientTargets
    
    # Custom adjustments
    custom_adjustments: Dict[str, float] = {}
    
    # Calculation metadata
    bmr: Optional[float] = None  # Basal Metabolic Rate
    tdee: Optional[float] = None  # Total Daily Energy Expenditure
    calculation_method: Optional[str] = None  # harris_benedict, mifflin_st_jeor, etc.
    
    # Preferences
    meal_distribution: Dict[str, float] = {
        "breakfast": 0.25,
        "lunch": 0.35,
        "dinner": 0.30,
        "snack": 0.10
    }
    
    # System fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "nutrition_profiles"
        indexes = [
            "user_id"
        ]


class DailyIntake(Document):
    """Daily nutrition intake tracking."""
    
    user_id: str
    date: datetime
    
    # Actual intake
    actual_calories: float = 0
    actual_protein_g: float = 0
    actual_carbs_g: float = 0
    actual_fat_g: float = 0
    actual_fiber_g: float = 0
    actual_sugar_g: float = 0
    actual_sodium_mg: float = 0
    
    # Micronutrients
    micronutrients: Dict[str, float] = {}
    
    # Meal breakdown
    meals: Dict[str, Dict[str, float]] = {
        "breakfast": {},
        "lunch": {},
        "dinner": {},
        "snack": {}
    }
    
    # Progress tracking
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    
    # Calculated metrics
    calories_remaining: Optional[float] = None
    protein_remaining_g: Optional[float] = None
    carbs_remaining_g: Optional[float] = None
    fat_remaining_g: Optional[float] = None
    
    # System fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "daily_intakes"
        indexes = [
            "user_id",
            "date",
            ["user_id", "date"]
        ]


# Pydantic schemas for API
class NutritionProfileCreate(BaseModel):
    """Schema for creating nutrition profile."""
    macro_targets: MacroTargets
    micronutrient_targets: Optional[MicronutrientTargets] = None
    custom_adjustments: Optional[Dict[str, float]] = {}
    meal_distribution: Optional[Dict[str, float]] = None


class NutritionProfileUpdate(BaseModel):
    """Schema for updating nutrition profile."""
    macro_targets: Optional[MacroTargets] = None
    micronutrient_targets: Optional[MicronutrientTargets] = None
    custom_adjustments: Optional[Dict[str, float]] = None
    meal_distribution: Optional[Dict[str, float]] = None


class NutritionProfileResponse(BaseModel):
    """Schema for nutrition profile response."""
    id: str
    user_id: str
    macro_targets: MacroTargets
    micronutrient_targets: MicronutrientTargets
    custom_adjustments: Dict[str, float]
    meal_distribution: Dict[str, float]
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    calculation_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DailyIntakeResponse(BaseModel):
    """Schema for daily intake response."""
    id: str
    user_id: str
    date: datetime
    actual_calories: float
    actual_protein_g: float
    actual_carbs_g: float
    actual_fat_g: float
    actual_fiber_g: float
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    calories_remaining: Optional[float] = None
    protein_remaining_g: Optional[float] = None
    carbs_remaining_g: Optional[float] = None
    fat_remaining_g: Optional[float] = None
    meals: Dict[str, Dict[str, float]]


class NutritionProgress(BaseModel):
    """Schema for nutrition progress tracking."""
    date_range: List[datetime]
    daily_intakes: List[DailyIntakeResponse]
    average_calories: float
    average_protein_g: float
    average_carbs_g: float
    average_fat_g: float
    target_adherence_percent: float
    trends: Dict[str, str]  # increasing, decreasing, stable
