"""
Feature engineering for nutrition recommendation models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
import joblib
from datetime import datetime, timedelta


class NutritionFeatureEngineer:
    """Feature engineering for nutrition recommendation models."""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []
    
    def create_user_features(self, user_data: Dict[str, Any]) -> np.ndarray:
        """
        Create feature vector from user profile data.
        
        Args:
            user_data: User profile dictionary
        
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Basic demographics
        features.extend([
            user_data.get('age', 30) / 100.0,  # Normalized age
            1.0 if user_data.get('gender') == 'male' else 0.0,  # Gender binary
            user_data.get('height_cm', 170) / 200.0,  # Normalized height
            user_data.get('weight_kg', 70) / 150.0,  # Normalized weight
        ])
        
        # Activity level encoding
        activity_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']
        activity_vector = [0.0] * len(activity_levels)
        user_activity = user_data.get('activity_level', 'moderately_active')
        if user_activity in activity_levels:
            activity_vector[activity_levels.index(user_activity)] = 1.0
        features.extend(activity_vector)
        
        # Goal encoding
        goals = ['weight_loss', 'weight_gain', 'muscle_gain', 'maintenance', 'health_improvement']
        goal_vector = [0.0] * len(goals)
        user_goal = user_data.get('primary_goal', 'maintenance')
        if user_goal in goals:
            goal_vector[goals.index(user_goal)] = 1.0
        features.extend(goal_vector)
        
        # Health conditions (binary features for common conditions)
        common_conditions = ['diabetes', 'hypertension', 'heart_disease', 'obesity', 'anemia', 'osteoporosis']
        health_vector = [0.0] * len(common_conditions)
        user_conditions = [condition.get('name', '').lower() for condition in user_data.get('health_conditions', [])]
        for i, condition in enumerate(common_conditions):
            if any(condition in user_condition for user_condition in user_conditions):
                health_vector[i] = 1.0
        features.extend(health_vector)
        
        # Dietary restrictions
        restrictions = ['vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'keto', 'paleo']
        restriction_vector = [0.0] * len(restrictions)
        user_restrictions = [restriction.get('type', '').lower() for restriction in user_data.get('dietary_restrictions', [])]
        for i, restriction in enumerate(restrictions):
            if restriction in user_restrictions:
                restriction_vector[i] = 1.0
        features.extend(restriction_vector)
        
        # BMI calculation
        height_m = user_data.get('height_cm', 170) / 100.0
        weight_kg = user_data.get('weight_kg', 70)
        bmi = weight_kg / (height_m ** 2) if height_m > 0 else 25.0
        features.append(bmi / 40.0)  # Normalized BMI
        
        # Target weight difference
        target_weight = user_data.get('target_weight_kg', weight_kg)
        weight_diff = (target_weight - weight_kg) / weight_kg if weight_kg > 0 else 0.0
        features.append(weight_diff)
        
        return np.array(features)
    
    def create_nutrition_features(self, nutrition_data: Dict[str, float]) -> np.ndarray:
        """
        Create feature vector from nutrition data.
        
        Args:
            nutrition_data: Nutrition intake dictionary
        
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Macronutrients (normalized)
        features.extend([
            nutrition_data.get('calories', 2000) / 3000.0,
            nutrition_data.get('protein_g', 50) / 200.0,
            nutrition_data.get('carbs_g', 250) / 500.0,
            nutrition_data.get('fat_g', 70) / 150.0,
            nutrition_data.get('fiber_g', 25) / 50.0,
            nutrition_data.get('sugar_g', 50) / 100.0,
            nutrition_data.get('sodium_mg', 2300) / 5000.0,
        ])
        
        # Micronutrients (normalized by RDA)
        micronutrients = {
            'vitamin_a_mcg': 900.0,
            'vitamin_c_mg': 90.0,
            'vitamin_d_mcg': 20.0,
            'calcium_mg': 1000.0,
            'iron_mg': 18.0,
            'potassium_mg': 3500.0,
            'magnesium_mg': 400.0,
            'zinc_mg': 11.0,
        }
        
        for nutrient, rda in micronutrients.items():
            value = nutrition_data.get(nutrient, rda * 0.5) / rda
            features.append(min(value, 3.0))  # Cap at 3x RDA
        
        # Macronutrient ratios
        total_calories = nutrition_data.get('calories', 2000)
        if total_calories > 0:
            protein_ratio = (nutrition_data.get('protein_g', 50) * 4) / total_calories
            carb_ratio = (nutrition_data.get('carbs_g', 250) * 4) / total_calories
            fat_ratio = (nutrition_data.get('fat_g', 70) * 9) / total_calories
        else:
            protein_ratio = carb_ratio = fat_ratio = 0.33
        
        features.extend([protein_ratio, carb_ratio, fat_ratio])
        
        return np.array(features)
    
    def create_temporal_features(self, food_history: List[Dict[str, Any]], days: int = 7) -> np.ndarray:
        """
        Create temporal features from food consumption history.
        
        Args:
            food_history: List of food consumption records
            days: Number of days to look back
        
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Initialize daily nutrition totals
        daily_nutrition = {}
        for i in range(days):
            date_key = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_nutrition[date_key] = {
                'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0
            }
        
        # Aggregate nutrition by day
        for record in food_history:
            record_date = record.get('date', datetime.now()).strftime('%Y-%m-%d')
            if record_date in daily_nutrition:
                daily_nutrition[record_date]['calories'] += record.get('calories', 0)
                daily_nutrition[record_date]['protein_g'] += record.get('protein_g', 0)
                daily_nutrition[record_date]['carbs_g'] += record.get('carbs_g', 0)
                daily_nutrition[record_date]['fat_g'] += record.get('fat_g', 0)
                daily_nutrition[record_date]['fiber_g'] += record.get('fiber_g', 0)
        
        # Calculate statistics
        calories_list = [day['calories'] for day in daily_nutrition.values()]
        protein_list = [day['protein_g'] for day in daily_nutrition.values()]
        carbs_list = [day['carbs_g'] for day in daily_nutrition.values()]
        fat_list = [day['fat_g'] for day in daily_nutrition.values()]
        
        # Mean, std, trend for each macronutrient
        for nutrient_list in [calories_list, protein_list, carbs_list, fat_list]:
            if len(nutrient_list) > 0:
                features.extend([
                    np.mean(nutrient_list),
                    np.std(nutrient_list),
                    np.polyfit(range(len(nutrient_list)), nutrient_list, 1)[0]  # Trend slope
                ])
            else:
                features.extend([0.0, 0.0, 0.0])
        
        # Meal timing patterns
        meal_counts = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        for record in food_history:
            meal_type = record.get('meal_type', 'snack')
            if meal_type in meal_counts:
                meal_counts[meal_type] += 1
        
        total_meals = sum(meal_counts.values())
        if total_meals > 0:
            features.extend([count / total_meals for count in meal_counts.values()])
        else:
            features.extend([0.25, 0.25, 0.25, 0.25])
        
        # Consistency score (how consistent is daily intake)
        if len(calories_list) > 1:
            cv_calories = np.std(calories_list) / np.mean(calories_list) if np.mean(calories_list) > 0 else 1.0
            consistency_score = max(0.0, 1.0 - cv_calories)
        else:
            consistency_score = 0.5
        features.append(consistency_score)
        
        return np.array(features)
    
    def create_food_preference_features(self, food_history: List[Dict[str, Any]]) -> np.ndarray:
        """
        Create features representing food preferences and patterns.
        
        Args:
            food_history: List of food consumption records
        
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Food category preferences
        categories = ['dairy', 'meat', 'vegetables', 'fruits', 'grains', 'nuts', 'beverages', 'sweets']
        category_counts = {cat: 0 for cat in categories}
        
        for record in food_history:
            food_category = record.get('food_category', '').lower()
            for category in categories:
                if category in food_category:
                    category_counts[category] += 1
                    break
        
        total_foods = len(food_history)
        if total_foods > 0:
            features.extend([count / total_foods for count in category_counts.values()])
        else:
            features.extend([0.125] * len(categories))
        
        # Cooking complexity preference (based on ingredient count)
        complexity_scores = []
        for record in food_history:
            # Estimate complexity based on food description length and type
            description = record.get('food_description', '')
            if 'raw' in description.lower() or 'fresh' in description.lower():
                complexity_scores.append(1.0)  # Simple
            elif 'prepared' in description.lower() or 'cooked' in description.lower():
                complexity_scores.append(2.0)  # Medium
            elif 'recipe' in description.lower() or len(description.split()) > 5:
                complexity_scores.append(3.0)  # Complex
            else:
                complexity_scores.append(2.0)  # Default medium
        
        avg_complexity = np.mean(complexity_scores) if complexity_scores else 2.0
        features.append(avg_complexity / 3.0)  # Normalized
        
        # Brand loyalty (how often user chooses branded vs generic foods)
        branded_count = sum(1 for record in food_history if record.get('brand_name'))
        brand_loyalty = branded_count / total_foods if total_foods > 0 else 0.5
        features.append(brand_loyalty)
        
        # Variety score (how diverse is the diet)
        unique_foods = len(set(record.get('fdc_id') for record in food_history))
        variety_score = unique_foods / total_foods if total_foods > 0 else 1.0
        features.append(min(variety_score, 1.0))
        
        return np.array(features)
    
    def fit_transform(self, user_data: List[Dict[str, Any]], nutrition_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Fit feature engineering pipeline and transform data.
        
        Args:
            user_data: List of user profile dictionaries
            nutrition_data: List of nutrition data dictionaries
        
        Returns:
            Transformed feature matrix
        """
        features_list = []
        
        for i, user in enumerate(user_data):
            user_features = self.create_user_features(user)
            nutrition_features = self.create_nutrition_features(nutrition_data[i])
            
            # Combine all features
            combined_features = np.concatenate([user_features, nutrition_features])
            features_list.append(combined_features)
        
        feature_matrix = np.array(features_list)
        
        # Fit and transform with standard scaler
        self.scaler = StandardScaler()
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        # Store feature names for interpretability
        self.feature_names = self._get_feature_names()
        
        return scaled_features
    
    def transform(self, user_data: Dict[str, Any], nutrition_data: Dict[str, Any] = None) -> np.ndarray:
        """
        Transform new data using fitted pipeline.
        
        Args:
            user_data: User profile dictionary
            nutrition_data: Nutrition data dictionary
        
        Returns:
            Transformed feature vector
        """
        user_features = self.create_user_features(user_data)
        
        if nutrition_data:
            nutrition_features = self.create_nutrition_features(nutrition_data)
            combined_features = np.concatenate([user_features, nutrition_features])
        else:
            # Use default nutrition values if not provided
            default_nutrition = {
                'calories': 2000, 'protein_g': 50, 'carbs_g': 250, 'fat_g': 70,
                'fiber_g': 25, 'sugar_g': 50, 'sodium_mg': 2300
            }
            nutrition_features = self.create_nutrition_features(default_nutrition)
            combined_features = np.concatenate([user_features, nutrition_features])
        
        # Reshape for single sample
        combined_features = combined_features.reshape(1, -1)
        
        # Scale using fitted scaler
        if hasattr(self, 'scaler'):
            return self.scaler.transform(combined_features)
        else:
            return combined_features
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for interpretability."""
        names = []
        
        # User features
        names.extend(['age_norm', 'gender_male', 'height_norm', 'weight_norm'])
        names.extend([f'activity_{level}' for level in ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']])
        names.extend([f'goal_{goal}' for goal in ['weight_loss', 'weight_gain', 'muscle_gain', 'maintenance', 'health_improvement']])
        names.extend([f'condition_{condition}' for condition in ['diabetes', 'hypertension', 'heart_disease', 'obesity', 'anemia', 'osteoporosis']])
        names.extend([f'restriction_{restriction}' for restriction in ['vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'keto', 'paleo']])
        names.extend(['bmi_norm', 'weight_diff'])
        
        # Nutrition features
        names.extend(['calories_norm', 'protein_norm', 'carbs_norm', 'fat_norm', 'fiber_norm', 'sugar_norm', 'sodium_norm'])
        names.extend(['vitamin_a_norm', 'vitamin_c_norm', 'vitamin_d_norm', 'calcium_norm', 'iron_norm', 'potassium_norm', 'magnesium_norm', 'zinc_norm'])
        names.extend(['protein_ratio', 'carb_ratio', 'fat_ratio'])
        
        return names
    
    def save_pipeline(self, filepath: str):
        """Save the fitted pipeline."""
        pipeline_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        joblib.dump(pipeline_data, filepath)
    
    def load_pipeline(self, filepath: str):
        """Load a fitted pipeline."""
        pipeline_data = joblib.load(filepath)
        self.scaler = pipeline_data['scaler']
        self.feature_names = pipeline_data['feature_names']
