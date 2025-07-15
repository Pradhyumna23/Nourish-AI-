"""
Helper utilities for the application.
"""

import hashlib
import secrets
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, salt: Optional[str] = None) -> str:
    """Hash a string with optional salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{text}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight and height."""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_category(bmi: float) -> str:
    """Get BMI category from BMI value."""
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"


def calculate_age_from_birthdate(birthdate: datetime) -> int:
    """Calculate age from birthdate."""
    today = datetime.now()
    age = today.year - birthdate.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < birthdate.month or (today.month == birthdate.month and today.day < birthdate.day):
        age -= 1
    
    return age


def format_nutrition_value(value: float, unit: str) -> str:
    """Format nutrition value for display."""
    if unit in ['kcal', 'calories']:
        return f"{value:.0f} {unit}"
    elif unit in ['g', 'mg', 'mcg']:
        if value < 1:
            return f"{value:.2f} {unit}"
        elif value < 10:
            return f"{value:.1f} {unit}"
        else:
            return f"{value:.0f} {unit}"
    else:
        return f"{value:.1f} {unit}"


def calculate_percentage_of_target(actual: float, target: float) -> float:
    """Calculate percentage of target achieved."""
    if target == 0:
        return 0
    return (actual / target) * 100


def get_nutrition_status(percentage: float) -> str:
    """Get nutrition status based on percentage of target."""
    if percentage < 50:
        return "critically_low"
    elif percentage < 80:
        return "below_target"
    elif percentage <= 120:
        return "on_target"
    elif percentage <= 150:
        return "above_target"
    else:
        return "excessive"


def calculate_calorie_deficit_surplus(actual_calories: float, target_calories: float) -> Dict[str, Any]:
    """Calculate calorie deficit or surplus."""
    difference = actual_calories - target_calories
    
    if difference > 0:
        return {
            "type": "surplus",
            "amount": difference,
            "percentage": (difference / target_calories) * 100
        }
    else:
        return {
            "type": "deficit",
            "amount": abs(difference),
            "percentage": (abs(difference) / target_calories) * 100
        }


def estimate_weight_change(calorie_difference: float, days: int) -> float:
    """
    Estimate weight change based on calorie difference.
    
    Assumes 3500 calories = 1 pound (0.45 kg)
    """
    total_calorie_difference = calorie_difference * days
    weight_change_pounds = total_calorie_difference / 3500
    weight_change_kg = weight_change_pounds * 0.453592
    
    return weight_change_kg


def get_meal_time_recommendations() -> Dict[str, Dict[str, int]]:
    """Get recommended meal times."""
    return {
        "breakfast": {"start": 6, "end": 10},
        "lunch": {"start": 11, "end": 15},
        "dinner": {"start": 17, "end": 21},
        "snack": {"start": 14, "end": 16}
    }


def is_appropriate_meal_time(meal_type: str, current_hour: int) -> bool:
    """Check if current time is appropriate for meal type."""
    recommendations = get_meal_time_recommendations()
    
    if meal_type not in recommendations:
        return True  # Allow snacks anytime
    
    meal_time = recommendations[meal_type]
    return meal_time["start"] <= current_hour <= meal_time["end"]


def calculate_macro_ratios(calories: float, protein_g: float, carbs_g: float, fat_g: float) -> Dict[str, float]:
    """Calculate macronutrient ratios."""
    if calories == 0:
        return {"protein": 0, "carbs": 0, "fat": 0}
    
    protein_calories = protein_g * 4
    carb_calories = carbs_g * 4
    fat_calories = fat_g * 9
    
    return {
        "protein": (protein_calories / calories) * 100,
        "carbs": (carb_calories / calories) * 100,
        "fat": (fat_calories / calories) * 100
    }


def get_nutrient_density_score(nutrients: Dict[str, float], calories: float) -> float:
    """
    Calculate a simple nutrient density score.
    
    Higher score indicates more nutrients per calorie.
    """
    if calories == 0:
        return 0
    
    # Key nutrients for scoring
    key_nutrients = {
        'protein_g': 4,      # Weight factor
        'fiber_g': 3,
        'vitamin_c_mg': 2,
        'calcium_mg': 2,
        'iron_mg': 3,
        'potassium_mg': 1
    }
    
    score = 0
    for nutrient, weight in key_nutrients.items():
        if nutrient in nutrients:
            # Normalize by typical daily values
            if nutrient == 'protein_g':
                normalized = min(nutrients[nutrient] / 50, 2)  # Cap at 2x
            elif nutrient == 'fiber_g':
                normalized = min(nutrients[nutrient] / 25, 2)
            elif nutrient == 'vitamin_c_mg':
                normalized = min(nutrients[nutrient] / 90, 2)
            elif nutrient == 'calcium_mg':
                normalized = min(nutrients[nutrient] / 1000, 2)
            elif nutrient == 'iron_mg':
                normalized = min(nutrients[nutrient] / 18, 2)
            elif nutrient == 'potassium_mg':
                normalized = min(nutrients[nutrient] / 3500, 2)
            else:
                normalized = 1
            
            score += normalized * weight
    
    # Normalize by calories (per 100 calories)
    return (score / calories) * 100


def format_time_duration(minutes: int) -> str:
    """Format time duration in a human-readable way."""
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minutes"


def get_seasonal_food_recommendations(month: int) -> List[str]:
    """Get seasonal food recommendations based on month."""
    seasonal_foods = {
        1: ["citrus fruits", "winter squash", "kale", "brussels sprouts"],  # January
        2: ["citrus fruits", "winter squash", "kale", "brussels sprouts"],  # February
        3: ["asparagus", "artichokes", "peas", "spring onions"],           # March
        4: ["asparagus", "artichokes", "peas", "spring greens"],           # April
        5: ["strawberries", "asparagus", "lettuce", "radishes"],           # May
        6: ["berries", "tomatoes", "zucchini", "corn"],                    # June
        7: ["berries", "tomatoes", "zucchini", "peaches"],                 # July
        8: ["tomatoes", "corn", "peaches", "melons"],                      # August
        9: ["apples", "pears", "squash", "sweet potatoes"],                # September
        10: ["apples", "pears", "pumpkin", "sweet potatoes"],              # October
        11: ["cranberries", "sweet potatoes", "winter squash", "kale"],    # November
        12: ["citrus fruits", "winter squash", "kale", "brussels sprouts"] # December
    }
    
    return seasonal_foods.get(month, [])


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    return filename[:255]


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def round_to_nearest(value: float, nearest: float = 0.5) -> float:
    """Round value to nearest specified increment."""
    return round(value / nearest) * nearest
