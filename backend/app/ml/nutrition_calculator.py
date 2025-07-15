"""
Nutrition calculation service using ML models and nutritional science.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Add ml-models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../ml-models/src'))

try:
    from recommendation_models import CalorieRecommendationModel, MacronutrientRecommendationModel
    from feature_engineering import NutritionFeatureEngineer
except ImportError:
    logger.warning("ML models not available, using fallback calculations")
    CalorieRecommendationModel = None
    MacronutrientRecommendationModel = None
    NutritionFeatureEngineer = None

from app.models.user import User
from app.models.nutrition import MacroTargets, MicronutrientTargets


class NutritionCalculatorService:
    """Service for calculating personalized nutrition recommendations."""
    
    def __init__(self):
        self.calorie_model = None
        self.macro_model = None
        self.feature_engineer = None
        
        # Try to load pre-trained models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained ML models if available."""
        try:
            if CalorieRecommendationModel:
                self.calorie_model = CalorieRecommendationModel()
                # Try to load pre-trained model
                model_path = "ml-models/trained/calorie_model.joblib"
                if os.path.exists(model_path):
                    self.calorie_model.load_model(model_path)
                    logger.info("Loaded pre-trained calorie model")
            
            if MacronutrientRecommendationModel:
                self.macro_model = MacronutrientRecommendationModel()
                model_path = "ml-models/trained/macro_model.joblib"
                if os.path.exists(model_path):
                    self.macro_model.load_model(model_path)
                    logger.info("Loaded pre-trained macro model")
                    
        except Exception as e:
            logger.warning(f"Could not load ML models: {e}")
    
    def calculate_bmr(self, user: User) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
        
        Args:
            user: User instance
        
        Returns:
            BMR in calories
        """
        if not user.weight_kg or not user.height_cm or not user.age:
            # Use default values if missing
            weight = user.weight_kg or 70
            height = user.height_cm or 170
            age = user.age or 30
        else:
            weight = user.weight_kg
            height = user.height_cm
            age = user.age
        
        if user.gender == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        return bmr
    
    def calculate_tdee(self, user: User) -> float:
        """
        Calculate Total Daily Energy Expenditure.
        
        Args:
            user: User instance
        
        Returns:
            TDEE in calories
        """
        bmr = self.calculate_bmr(user)
        
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        
        multiplier = activity_multipliers.get(user.activity_level or 'moderately_active', 1.55)
        return bmr * multiplier
    
    def calculate_calorie_target(self, user: User) -> float:
        """
        Calculate personalized calorie target.
        
        Args:
            user: User instance
        
        Returns:
            Daily calorie target
        """
        # If user has a custom target, use it
        if user.target_calories:
            return user.target_calories
        
        # Use ML model if available and trained
        if self.calorie_model and self.calorie_model.is_fitted:
            try:
                user_profile = self._user_to_dict(user)
                prediction = self.calorie_model.predict(user_profile)
                return prediction.get('calories', self.calculate_tdee(user))
            except Exception as e:
                logger.warning(f"ML calorie prediction failed: {e}")
        
        # Fallback to traditional calculation
        tdee = self.calculate_tdee(user)
        
        # Adjust based on goals
        if user.primary_goal == 'weight_loss':
            return tdee - 500  # 500 calorie deficit
        elif user.primary_goal == 'weight_gain':
            return tdee + 500  # 500 calorie surplus
        elif user.primary_goal == 'muscle_gain':
            return tdee + 300  # Moderate surplus
        else:
            return tdee  # Maintenance
    
    def calculate_macro_targets(self, user: User, total_calories: float) -> MacroTargets:
        """
        Calculate macronutrient targets.
        
        Args:
            user: User instance
            total_calories: Total daily calories
        
        Returns:
            MacroTargets instance
        """
        # Use ML model if available and trained
        if self.macro_model and self.macro_model.is_fitted:
            try:
                user_profile = self._user_to_dict(user)
                prediction = self.macro_model.predict(user_profile)
                
                return MacroTargets(
                    calories=total_calories,
                    protein_g=prediction.get('protein_g', 50),
                    carbs_g=prediction.get('carbs_g', 250),
                    fat_g=prediction.get('fat_g', 70),
                    fiber_g=prediction.get('fiber_g', 25)
                )
            except Exception as e:
                logger.warning(f"ML macro prediction failed: {e}")
        
        # Fallback to traditional calculation
        weight = user.weight_kg or 70
        goal = user.primary_goal or 'maintenance'
        activity_level = user.activity_level or 'moderately_active'
        
        # Protein calculation (g/kg body weight)
        if goal == 'muscle_gain':
            protein_per_kg = 2.2
        elif goal == 'weight_loss':
            protein_per_kg = 2.0
        elif activity_level in ['very_active', 'extremely_active']:
            protein_per_kg = 1.8
        else:
            protein_per_kg = 1.2
        
        protein_g = weight * protein_per_kg
        protein_calories = protein_g * 4
        
        # Fat calculation (percentage of total calories)
        if goal == 'muscle_gain':
            fat_percent = 0.25
        elif goal == 'weight_loss':
            fat_percent = 0.30
        else:
            fat_percent = 0.28
        
        fat_calories = total_calories * fat_percent
        fat_g = fat_calories / 9
        
        # Carbs (remaining calories)
        carb_calories = total_calories - protein_calories - fat_calories
        carb_g = max(0, carb_calories / 4)
        
        # Fiber (14g per 1000 calories, max 35g)
        fiber_g = min(35, total_calories / 1000 * 14)
        
        # Calculate percentages
        protein_percent = (protein_calories / total_calories) * 100
        carb_percent = (carb_calories / total_calories) * 100
        fat_percent = (fat_calories / total_calories) * 100
        
        return MacroTargets(
            calories=total_calories,
            protein_g=protein_g,
            carbs_g=carb_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            protein_percent=protein_percent,
            carbs_percent=carb_percent,
            fat_percent=fat_percent
        )
    
    def calculate_micronutrient_targets(self, user: User) -> MicronutrientTargets:
        """
        Calculate micronutrient targets based on RDA/DRI.
        
        Args:
            user: User instance
        
        Returns:
            MicronutrientTargets instance
        """
        age = user.age or 30
        gender = user.gender or 'male'
        
        # Base RDA values (can be adjusted based on age, gender, conditions)
        if gender == 'male':
            targets = {
                'vitamin_a_mcg': 900,
                'vitamin_c_mg': 90,
                'vitamin_d_mcg': 20,
                'vitamin_e_mg': 15,
                'vitamin_k_mcg': 120,
                'thiamin_mg': 1.2,
                'riboflavin_mg': 1.3,
                'niacin_mg': 16,
                'vitamin_b6_mg': 1.7 if age > 50 else 1.3,
                'folate_mcg': 400,
                'vitamin_b12_mcg': 2.4,
                'calcium_mg': 1200 if age > 70 else 1000,
                'iron_mg': 8,
                'magnesium_mg': 420 if age > 30 else 400,
                'phosphorus_mg': 700,
                'potassium_mg': 3400,
                'sodium_mg': 2300,  # Upper limit
                'zinc_mg': 11
            }
        else:  # female
            targets = {
                'vitamin_a_mcg': 700,
                'vitamin_c_mg': 75,
                'vitamin_d_mcg': 20,
                'vitamin_e_mg': 15,
                'vitamin_k_mcg': 90,
                'thiamin_mg': 1.1,
                'riboflavin_mg': 1.1,
                'niacin_mg': 14,
                'vitamin_b6_mg': 1.5 if age > 50 else 1.3,
                'folate_mcg': 400,
                'vitamin_b12_mcg': 2.4,
                'calcium_mg': 1200 if age > 50 else 1000,
                'iron_mg': 8 if age > 50 else 18,
                'magnesium_mg': 320 if age > 30 else 310,
                'phosphorus_mg': 700,
                'potassium_mg': 2600,
                'sodium_mg': 2300,  # Upper limit
                'zinc_mg': 8
            }
        
        # Adjust for health conditions
        for condition in user.health_conditions:
            condition_name = condition.name.lower()
            if 'anemia' in condition_name:
                targets['iron_mg'] *= 1.5
            elif 'osteoporosis' in condition_name:
                targets['calcium_mg'] *= 1.2
                targets['vitamin_d_mcg'] *= 1.5
            elif 'hypertension' in condition_name:
                targets['sodium_mg'] = 1500  # Lower sodium limit
                targets['potassium_mg'] *= 1.2
        
        return MicronutrientTargets(**targets)
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User instance to dictionary for ML models."""
        return {
            'age': user.age,
            'gender': user.gender,
            'height_cm': user.height_cm,
            'weight_kg': user.weight_kg,
            'activity_level': user.activity_level,
            'primary_goal': user.primary_goal,
            'target_weight_kg': user.target_weight_kg,
            'health_conditions': [{'name': condition.name} for condition in user.health_conditions],
            'dietary_restrictions': [{'type': restriction.type} for restriction in user.dietary_restrictions],
            'allergies': user.allergies
        }
    
    def get_nutrition_recommendations(self, user: User) -> Dict[str, Any]:
        """
        Get comprehensive nutrition recommendations for a user.
        
        Args:
            user: User instance
        
        Returns:
            Dictionary with all nutrition recommendations
        """
        try:
            # Calculate calorie target
            calorie_target = self.calculate_calorie_target(user)
            
            # Calculate macro targets
            macro_targets = self.calculate_macro_targets(user, calorie_target)
            
            # Calculate micronutrient targets
            micro_targets = self.calculate_micronutrient_targets(user)
            
            # Calculate BMR and TDEE for reference
            bmr = self.calculate_bmr(user)
            tdee = self.calculate_tdee(user)
            
            return {
                'calorie_target': calorie_target,
                'macro_targets': macro_targets,
                'micronutrient_targets': micro_targets,
                'bmr': bmr,
                'tdee': tdee,
                'calculation_method': 'ml_enhanced' if self.calorie_model else 'traditional',
                'calculated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error calculating nutrition recommendations: {e}")
            raise
