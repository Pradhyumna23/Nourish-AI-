"""
Machine learning models for nutrition recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import joblib
from datetime import datetime
import logging

from .feature_engineering import NutritionFeatureEngineer


class NutritionRecommendationModel:
    """Base class for nutrition recommendation models."""
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.feature_engineer = NutritionFeatureEngineer()
        self.is_fitted = False
        self.feature_importance = None
        self.performance_metrics = {}
        
        # Initialize model based on type
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the ML model based on type."""
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        elif self.model_type == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        elif self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        elif self.model_type == "linear":
            self.model = Ridge(alpha=1.0)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def prepare_training_data(self, user_profiles: List[Dict], nutrition_targets: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from user profiles and nutrition targets.
        
        Args:
            user_profiles: List of user profile dictionaries
            nutrition_targets: List of nutrition target dictionaries
        
        Returns:
            Tuple of (features, targets)
        """
        # Create features using feature engineering
        X = self.feature_engineer.fit_transform(user_profiles, nutrition_targets)
        
        # Create target matrix (calories, protein, carbs, fat, fiber)
        y = []
        for target in nutrition_targets:
            target_vector = [
                target.get('calories', 2000),
                target.get('protein_g', 50),
                target.get('carbs_g', 250),
                target.get('fat_g', 70),
                target.get('fiber_g', 25)
            ]
            y.append(target_vector)
        
        return X, np.array(y)
    
    def train(self, user_profiles: List[Dict], nutrition_targets: List[Dict], validation_split: float = 0.2):
        """
        Train the recommendation model.
        
        Args:
            user_profiles: List of user profile dictionaries
            nutrition_targets: List of nutrition target dictionaries
            validation_split: Fraction of data to use for validation
        """
        logging.info(f"Training {self.model_type} model with {len(user_profiles)} samples")
        
        # Prepare data
        X, y = self.prepare_training_data(user_profiles, nutrition_targets)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Train model for each target (multi-output regression)
        self.models = {}
        target_names = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g']
        
        for i, target_name in enumerate(target_names):
            # Clone the base model for each target
            if self.model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100, max_depth=10, min_samples_split=5,
                    min_samples_leaf=2, random_state=42
                )
            elif self.model_type == "xgboost":
                model = xgb.XGBRegressor(
                    n_estimators=100, max_depth=6, learning_rate=0.1,
                    subsample=0.8, colsample_bytree=0.8, random_state=42
                )
            elif self.model_type == "gradient_boosting":
                model = GradientBoostingRegressor(
                    n_estimators=100, max_depth=6, learning_rate=0.1,
                    subsample=0.8, random_state=42
                )
            elif self.model_type == "linear":
                model = Ridge(alpha=1.0)
            
            # Train model
            model.fit(X_train, y_train[:, i])
            self.models[target_name] = model
            
            # Evaluate on validation set
            y_pred = model.predict(X_val)
            mse = mean_squared_error(y_val[:, i], y_pred)
            mae = mean_absolute_error(y_val[:, i], y_pred)
            r2 = r2_score(y_val[:, i], y_pred)
            
            self.performance_metrics[target_name] = {
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'rmse': np.sqrt(mse)
            }
            
            logging.info(f"{target_name} - MSE: {mse:.2f}, MAE: {mae:.2f}, R2: {r2:.3f}")
        
        # Calculate feature importance (using first model as representative)
        if hasattr(self.models['calories'], 'feature_importances_'):
            self.feature_importance = self.models['calories'].feature_importances_
        
        self.is_fitted = True
        logging.info("Model training completed")
    
    def predict(self, user_profile: Dict, current_nutrition: Optional[Dict] = None) -> Dict[str, float]:
        """
        Predict nutrition recommendations for a user.
        
        Args:
            user_profile: User profile dictionary
            current_nutrition: Current nutrition intake (optional)
        
        Returns:
            Dictionary with nutrition recommendations
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before making predictions")
        
        # Transform user data to features
        X = self.feature_engineer.transform(user_profile, current_nutrition)
        
        # Make predictions for each target
        predictions = {}
        target_names = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g']
        
        for target_name in target_names:
            pred = self.models[target_name].predict(X)[0]
            predictions[target_name] = max(0, pred)  # Ensure non-negative
        
        return predictions
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top feature importances.
        
        Args:
            top_n: Number of top features to return
        
        Returns:
            List of (feature_name, importance) tuples
        """
        if self.feature_importance is None:
            return []
        
        feature_names = self.feature_engineer.feature_names
        importance_pairs = list(zip(feature_names, self.feature_importance))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)
        
        return importance_pairs[:top_n]
    
    def optimize_hyperparameters(self, user_profiles: List[Dict], nutrition_targets: List[Dict]):
        """
        Optimize model hyperparameters using grid search.
        
        Args:
            user_profiles: List of user profile dictionaries
            nutrition_targets: List of nutrition target dictionaries
        """
        logging.info("Starting hyperparameter optimization")
        
        X, y = self.prepare_training_data(user_profiles, nutrition_targets)
        
        # Define parameter grids for different models
        if self.model_type == "random_forest":
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif self.model_type == "xgboost":
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0]
            }
        elif self.model_type == "gradient_boosting":
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0]
            }
        elif self.model_type == "linear":
            param_grid = {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        
        # Optimize for calories prediction (representative)
        grid_search = GridSearchCV(
            self.model, param_grid, cv=5, scoring='neg_mean_squared_error',
            n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X, y[:, 0])  # Use calories as target
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        logging.info(f"Best parameters: {grid_search.best_params_}")
        logging.info(f"Best CV score: {-grid_search.best_score_:.2f}")
    
    def save_model(self, filepath: str):
        """Save the trained model."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'models': self.models,
            'feature_engineer': self.feature_engineer,
            'model_type': self.model_type,
            'performance_metrics': self.performance_metrics,
            'feature_importance': self.feature_importance,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logging.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model."""
        model_data = joblib.load(filepath)
        
        self.models = model_data['models']
        self.feature_engineer = model_data['feature_engineer']
        self.model_type = model_data['model_type']
        self.performance_metrics = model_data.get('performance_metrics', {})
        self.feature_importance = model_data.get('feature_importance')
        self.is_fitted = True
        
        logging.info(f"Model loaded from {filepath}")


class CalorieRecommendationModel(NutritionRecommendationModel):
    """Specialized model for calorie recommendations."""
    
    def __init__(self):
        super().__init__(model_type="xgboost")
    
    def calculate_bmr(self, user_profile: Dict) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
        
        Args:
            user_profile: User profile dictionary
        
        Returns:
            BMR in calories
        """
        weight = user_profile.get('weight_kg', 70)
        height = user_profile.get('height_cm', 170)
        age = user_profile.get('age', 30)
        gender = user_profile.get('gender', 'male')
        
        if gender == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        return bmr
    
    def calculate_tdee(self, user_profile: Dict) -> float:
        """
        Calculate Total Daily Energy Expenditure.
        
        Args:
            user_profile: User profile dictionary
        
        Returns:
            TDEE in calories
        """
        bmr = self.calculate_bmr(user_profile)
        activity_level = user_profile.get('activity_level', 'moderately_active')
        
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.55)
        return bmr * multiplier
    
    def adjust_for_goals(self, tdee: float, goal: str, target_weight: Optional[float] = None, current_weight: Optional[float] = None) -> float:
        """
        Adjust calorie target based on user goals.
        
        Args:
            tdee: Total Daily Energy Expenditure
            goal: User's primary goal
            target_weight: Target weight in kg
            current_weight: Current weight in kg
        
        Returns:
            Adjusted calorie target
        """
        if goal == 'weight_loss':
            return tdee - 500  # 500 calorie deficit for ~1 lb/week loss
        elif goal == 'weight_gain':
            return tdee + 500  # 500 calorie surplus for ~1 lb/week gain
        elif goal == 'muscle_gain':
            return tdee + 300  # Moderate surplus for muscle gain
        else:  # maintenance or health_improvement
            return tdee


class MacronutrientRecommendationModel(NutritionRecommendationModel):
    """Specialized model for macronutrient distribution recommendations."""
    
    def __init__(self):
        super().__init__(model_type="random_forest")
    
    def get_macro_distribution(self, user_profile: Dict, total_calories: float) -> Dict[str, float]:
        """
        Calculate macronutrient distribution based on user profile.
        
        Args:
            user_profile: User profile dictionary
            total_calories: Total daily calories
        
        Returns:
            Dictionary with macro targets in grams
        """
        goal = user_profile.get('primary_goal', 'maintenance')
        activity_level = user_profile.get('activity_level', 'moderately_active')
        weight = user_profile.get('weight_kg', 70)
        
        # Base protein requirement (g/kg body weight)
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
        
        # Fat percentage based on goals
        if goal == 'muscle_gain':
            fat_percent = 0.25
        elif goal == 'weight_loss':
            fat_percent = 0.30
        else:
            fat_percent = 0.28
        
        fat_calories = total_calories * fat_percent
        fat_g = fat_calories / 9
        
        # Remaining calories from carbs
        carb_calories = total_calories - protein_calories - fat_calories
        carb_g = max(0, carb_calories / 4)
        
        # Fiber recommendation
        fiber_g = min(35, total_calories / 1000 * 14)  # 14g per 1000 calories, max 35g
        
        return {
            'protein_g': protein_g,
            'carbs_g': carb_g,
            'fat_g': fat_g,
            'fiber_g': fiber_g
        }
