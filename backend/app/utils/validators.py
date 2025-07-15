"""
Validation utilities for the application.
"""

import re
from typing import List, Optional
from datetime import datetime, date


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    return len(issues) == 0, issues


def validate_age(age: int) -> bool:
    """Validate age is within reasonable range."""
    return 13 <= age <= 120


def validate_weight(weight: float) -> bool:
    """Validate weight is within reasonable range (kg)."""
    return 20.0 <= weight <= 500.0


def validate_height(height: float) -> bool:
    """Validate height is within reasonable range (cm)."""
    return 100.0 <= height <= 250.0


def validate_date_not_future(target_date: date) -> bool:
    """Validate that date is not in the future."""
    return target_date <= date.today()


def validate_meal_type(meal_type: str) -> bool:
    """Validate meal type is one of the allowed values."""
    allowed_types = ['breakfast', 'lunch', 'dinner', 'snack']
    return meal_type.lower() in allowed_types


def validate_nutrition_value(value: float, nutrient_type: str) -> bool:
    """Validate nutrition values are within reasonable ranges."""
    ranges = {
        'calories': (0, 10000),
        'protein_g': (0, 500),
        'carbs_g': (0, 1000),
        'fat_g': (0, 300),
        'fiber_g': (0, 100),
        'sugar_g': (0, 500),
        'sodium_mg': (0, 10000),
        'vitamin_a_mcg': (0, 5000),
        'vitamin_c_mg': (0, 2000),
        'vitamin_d_mcg': (0, 100),
        'calcium_mg': (0, 3000),
        'iron_mg': (0, 50),
        'potassium_mg': (0, 10000)
    }
    
    if nutrient_type not in ranges:
        return True  # Unknown nutrient, allow it
    
    min_val, max_val = ranges[nutrient_type]
    return min_val <= value <= max_val


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitize string input by removing harmful characters and limiting length."""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    return sanitized[:max_length].strip()


def validate_fdc_id(fdc_id: int) -> bool:
    """Validate USDA FDC ID format."""
    return isinstance(fdc_id, int) and fdc_id > 0


def validate_quantity(quantity: float) -> bool:
    """Validate food quantity is positive and reasonable."""
    return 0.01 <= quantity <= 1000.0


def validate_rating(rating: int) -> bool:
    """Validate rating is within 1-5 range."""
    return 1 <= rating <= 5


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_user_profile_data(data: dict) -> List[str]:
    """
    Validate user profile data comprehensively.
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Age validation
    if 'age' in data and data['age'] is not None:
        if not validate_age(data['age']):
            errors.append("Age must be between 13 and 120 years")
    
    # Weight validation
    if 'weight_kg' in data and data['weight_kg'] is not None:
        if not validate_weight(data['weight_kg']):
            errors.append("Weight must be between 20 and 500 kg")
    
    # Height validation
    if 'height_cm' in data and data['height_cm'] is not None:
        if not validate_height(data['height_cm']):
            errors.append("Height must be between 100 and 250 cm")
    
    # Target weight validation
    if 'target_weight_kg' in data and data['target_weight_kg'] is not None:
        if not validate_weight(data['target_weight_kg']):
            errors.append("Target weight must be between 20 and 500 kg")
    
    # Target calories validation
    if 'target_calories' in data and data['target_calories'] is not None:
        if not (800 <= data['target_calories'] <= 5000):
            errors.append("Target calories must be between 800 and 5000")
    
    return errors


def validate_food_log_data(data: dict) -> List[str]:
    """
    Validate food logging data.
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # FDC ID validation
    if 'fdc_id' not in data or not validate_fdc_id(data['fdc_id']):
        errors.append("Valid FDC ID is required")
    
    # Date validation
    if 'date' in data:
        try:
            log_date = data['date']
            if isinstance(log_date, str):
                log_date = datetime.fromisoformat(log_date).date()
            elif isinstance(log_date, datetime):
                log_date = log_date.date()
            
            if not validate_date_not_future(log_date):
                errors.append("Date cannot be in the future")
        except (ValueError, TypeError):
            errors.append("Invalid date format")
    
    # Meal type validation
    if 'meal_type' not in data or not validate_meal_type(data['meal_type']):
        errors.append("Valid meal type is required (breakfast, lunch, dinner, snack)")
    
    # Quantity validation
    if 'quantity' not in data or not validate_quantity(data['quantity']):
        errors.append("Quantity must be between 0.01 and 1000")
    
    # Unit validation
    if 'unit' not in data or not data['unit'].strip():
        errors.append("Unit is required")
    
    return errors


def validate_recommendation_feedback(data: dict) -> List[str]:
    """
    Validate recommendation feedback data.
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Rating validation
    if 'rating' in data and data['rating'] is not None:
        if not validate_rating(data['rating']):
            errors.append("Rating must be between 1 and 5")
    
    # Feedback text validation
    if 'feedback' in data and data['feedback'] is not None:
        if len(data['feedback']) > 1000:
            errors.append("Feedback text cannot exceed 1000 characters")
    
    return errors
