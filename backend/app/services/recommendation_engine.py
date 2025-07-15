"""
Core recommendation engine that combines ML predictions with nutritional science.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from loguru import logger
import random
from enum import Enum

from app.models.user import User
from app.models.food import Food, FoodItem
from app.models.nutrition import NutritionProfile, DailyIntake
from app.models.recommendation import (
    Recommendation, RecommendationType, ConfidenceLevel,
    FoodSuggestion, MealPlan, NutrientAdjustment
)
from app.services.food import FoodService
from app.services.openai_service import OpenAIService
from app.ml.nutrition_calculator import NutritionCalculatorService


class RecommendationPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFORMATIONAL = 5


class RecommendationEngine:
    """Core recommendation engine for personalized nutrition advice."""
    
    def __init__(self):
        self.food_service = FoodService()
        self.openai_service = OpenAIService()
        self.nutrition_calculator = NutritionCalculatorService()
        
        # Nutritional science rules and thresholds
        self.nutrient_thresholds = {
            'protein_deficit_threshold': 0.8,  # 80% of target
            'fiber_deficit_threshold': 0.7,   # 70% of target
            'vitamin_deficit_threshold': 0.6, # 60% of RDA
            'excess_threshold': 1.5,          # 150% of target
            'critical_threshold': 0.5         # 50% of target (critical)
        }
    
    async def generate_comprehensive_recommendations(
        self, 
        user: User,
        current_intake: Optional[Dict[str, float]] = None,
        meal_type: Optional[str] = None
    ) -> List[Recommendation]:
        """
        Generate comprehensive recommendations for a user.
        
        Args:
            user: User instance
            current_intake: Current daily nutrition intake
            meal_type: Specific meal type to focus on
        
        Returns:
            List of Recommendation instances
        """
        recommendations = []
        
        try:
            # Get user's nutrition profile and targets
            nutrition_profile = await self._get_or_create_nutrition_profile(user)
            
            # Get current intake if not provided
            if current_intake is None:
                current_intake = await self._get_current_daily_intake(user)
            
            # Generate different types of recommendations
            recommendations.extend(await self._generate_nutrient_gap_recommendations(user, nutrition_profile, current_intake))
            recommendations.extend(await self._generate_food_suggestions(user, nutrition_profile, current_intake, meal_type))
            recommendations.extend(await self._generate_meal_plan_recommendations(user, nutrition_profile))
            recommendations.extend(await self._generate_health_optimization_recommendations(user, current_intake))
            
            # Sort by priority and confidence
            recommendations.sort(key=lambda x: (x.priority, -x.model_confidence))
            
            # Limit to top recommendations
            return recommendations[:10]
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {e}")
            return []
    
    async def _get_or_create_nutrition_profile(self, user: User) -> NutritionProfile:
        """Get or create nutrition profile for user."""
        profile = await NutritionProfile.find_one({"user_id": str(user.id)})
        
        if not profile:
            # Create new profile using nutrition calculator
            recommendations = self.nutrition_calculator.get_nutrition_recommendations(user)
            
            profile = NutritionProfile(
                user_id=str(user.id),
                macro_targets=recommendations['macro_targets'],
                micronutrient_targets=recommendations['micronutrient_targets'],
                bmr=recommendations['bmr'],
                tdee=recommendations['tdee'],
                calculation_method=recommendations['calculation_method']
            )
            await profile.insert()
        
        return profile
    
    async def _get_current_daily_intake(self, user: User) -> Dict[str, float]:
        """Get current daily nutrition intake for user."""
        today = date.today()
        daily_intake = await DailyIntake.find_one({
            "user_id": str(user.id),
            "date": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lte": datetime.combine(today, datetime.max.time())
            }
        })
        
        if daily_intake:
            return {
                'calories': daily_intake.actual_calories,
                'protein_g': daily_intake.actual_protein_g,
                'carbs_g': daily_intake.actual_carbs_g,
                'fat_g': daily_intake.actual_fat_g,
                'fiber_g': daily_intake.actual_fiber_g,
                **daily_intake.micronutrients
            }
        
        return {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0}
    
    async def _generate_nutrient_gap_recommendations(
        self, 
        user: User, 
        nutrition_profile: NutritionProfile,
        current_intake: Dict[str, float]
    ) -> List[Recommendation]:
        """Generate recommendations based on nutrient gaps."""
        recommendations = []
        
        # Analyze macronutrient gaps
        macro_targets = nutrition_profile.macro_targets
        nutrient_adjustments = []
        
        # Check each macronutrient
        macros = {
            'calories': macro_targets.calories,
            'protein_g': macro_targets.protein_g,
            'carbs_g': macro_targets.carbs_g,
            'fat_g': macro_targets.fat_g,
            'fiber_g': macro_targets.fiber_g
        }
        
        for nutrient, target in macros.items():
            current = current_intake.get(nutrient, 0)
            ratio = current / target if target > 0 else 0
            
            if ratio < self.nutrient_thresholds['critical_threshold']:
                priority = RecommendationPriority.CRITICAL
                severity = "critical"
            elif ratio < self.nutrient_thresholds['protein_deficit_threshold']:
                priority = RecommendationPriority.HIGH
                severity = "high"
            elif ratio > self.nutrient_thresholds['excess_threshold']:
                priority = RecommendationPriority.MEDIUM
                severity = "excess"
            else:
                continue  # Within acceptable range
            
            gap = target - current
            adjustment = NutrientAdjustment(
                nutrient_name=nutrient,
                current_intake=current,
                recommended_intake=target,
                adjustment_amount=abs(gap),
                adjustment_direction="increase" if gap > 0 else "decrease",
                unit="kcal" if nutrient == "calories" else "g",
                reason=self._get_nutrient_gap_reason(nutrient, ratio, user),
                health_impact=self._get_health_impact(nutrient, severity),
                food_sources=self._get_food_sources_for_nutrient(nutrient)
            )
            nutrient_adjustments.append(adjustment)
        
        if nutrient_adjustments:
            # Create recommendation
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.NUTRIENT_ADJUSTMENT,
                title="Nutrition Balance Optimization",
                description="Adjust your nutrient intake to better meet your daily targets",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=nutrient_adjustments,
                model_version="1.0",
                model_confidence=0.85,
                features_used=["current_intake", "targets", "user_profile"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=[condition.name for condition in user.health_conditions],
                dietary_restrictions=[restriction.type for restriction in user.dietary_restrictions],
                priority=min([adj for adj in nutrient_adjustments], key=lambda x: 1 if "critical" in x.reason.lower() else 2).priority if nutrient_adjustments else 3,
                expected_impact="high" if any("critical" in adj.reason.lower() for adj in nutrient_adjustments) else "medium",
                implementation_difficulty="easy",
                time_horizon="immediate"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_food_suggestions(
        self,
        user: User,
        nutrition_profile: NutritionProfile,
        current_intake: Dict[str, float],
        meal_type: Optional[str] = None
    ) -> List[Recommendation]:
        """Generate specific food suggestions to meet nutrition goals."""
        recommendations = []
        
        try:
            # Determine which nutrients need attention
            macro_targets = nutrition_profile.macro_targets
            deficit_nutrients = []
            
            for nutrient in ['protein_g', 'fiber_g']:
                current = current_intake.get(nutrient, 0)
                target = getattr(macro_targets, nutrient)
                if current < target * 0.8:  # Less than 80% of target
                    deficit_nutrients.append(nutrient)
            
            if not deficit_nutrients:
                return recommendations
            
            # Get food suggestions using OpenAI
            user_profile = {
                'age': user.age,
                'gender': user.gender,
                'activity_level': user.activity_level,
                'primary_goal': user.primary_goal,
                'health_conditions': [condition.name for condition in user.health_conditions]
            }
            
            # Calculate remaining nutrition needs
            remaining_calories = max(0, macro_targets.calories - current_intake.get('calories', 0))
            nutrition_targets = {
                'calories': remaining_calories * 0.3,  # For this meal
                'protein_g': max(0, macro_targets.protein_g - current_intake.get('protein_g', 0)) * 0.3,
                'carbs_g': max(0, macro_targets.carbs_g - current_intake.get('carbs_g', 0)) * 0.3,
                'fat_g': max(0, macro_targets.fat_g - current_intake.get('fat_g', 0)) * 0.3
            }
            
            dietary_restrictions = [restriction.type for restriction in user.dietary_restrictions]
            target_meal_type = meal_type or self._determine_next_meal()
            
            # Generate AI suggestions
            ai_suggestions = await self.openai_service.generate_meal_suggestions(
                user_profile=user_profile,
                nutrition_targets=nutrition_targets,
                dietary_restrictions=dietary_restrictions,
                meal_type=target_meal_type
            )
            
            if ai_suggestions:
                food_suggestions = []
                
                for suggestion in ai_suggestions[:3]:  # Top 3 suggestions
                    # Convert AI suggestion to FoodSuggestion
                    food_suggestion = FoodSuggestion(
                        fdc_id=0,  # Placeholder - would need food matching
                        food_name=suggestion.get('name', 'Unknown'),
                        serving_size=1.0,
                        serving_unit="serving",
                        calories=suggestion.get('estimated_nutrition', {}).get('calories', 0),
                        protein_g=suggestion.get('estimated_nutrition', {}).get('protein_g', 0),
                        carbs_g=suggestion.get('estimated_nutrition', {}).get('carbs_g', 0),
                        fat_g=suggestion.get('estimated_nutrition', {}).get('fat_g', 0),
                        reason=suggestion.get('rationale', 'Nutritionally balanced option'),
                        meal_type=target_meal_type,
                        priority_score=0.8,
                        nutritional_benefits=deficit_nutrients,
                        matches_dietary_restrictions=True,
                        allergen_warnings=self._check_allergens(suggestion, user.allergies)
                    )
                    food_suggestions.append(food_suggestion)
                
                # Create recommendation
                recommendation = Recommendation(
                    user_id=str(user.id),
                    recommendation_type=RecommendationType.FOOD_SUGGESTION,
                    title=f"Smart {target_meal_type.title()} Suggestions",
                    description=f"Personalized food recommendations to help you meet your {', '.join(deficit_nutrients)} goals",
                    confidence_level=ConfidenceLevel.MEDIUM,
                    food_suggestions=food_suggestions,
                    model_version="1.0",
                    model_confidence=0.75,
                    features_used=["nutrition_gaps", "user_preferences", "ai_analysis"],
                    user_goals=[user.primary_goal] if user.primary_goal else [],
                    health_conditions=[condition.name for condition in user.health_conditions],
                    dietary_restrictions=dietary_restrictions,
                    priority=RecommendationPriority.MEDIUM.value,
                    expected_impact="medium",
                    implementation_difficulty="easy",
                    time_horizon="immediate"
                )
                recommendations.append(recommendation)
        
        except Exception as e:
            logger.error(f"Error generating food suggestions: {e}")
        
        return recommendations
    
    async def _generate_meal_plan_recommendations(
        self,
        user: User,
        nutrition_profile: NutritionProfile
    ) -> List[Recommendation]:
        """Generate meal plan recommendations."""
        recommendations = []
        
        try:
            # Check if user would benefit from a meal plan
            recent_logs = await FoodItem.find({
                "user_id": str(user.id),
                "date": {"$gte": datetime.now() - timedelta(days=3)}
            }).to_list()
            
            # If user has inconsistent logging or expressed interest in meal planning
            if len(recent_logs) < 5:  # Less than 5 food logs in 3 days
                user_profile = {
                    'age': user.age,
                    'gender': user.gender,
                    'activity_level': user.activity_level,
                    'primary_goal': user.primary_goal,
                    'health_conditions': [condition.name for condition in user.health_conditions]
                }
                
                # Generate a simple daily meal plan
                macro_targets = nutrition_profile.macro_targets
                meal_distribution = nutrition_profile.meal_distribution
                
                daily_meals = {}
                for meal_type, percentage in meal_distribution.items():
                    meal_calories = macro_targets.calories * percentage
                    meal_targets = {
                        'calories': meal_calories,
                        'protein_g': macro_targets.protein_g * percentage,
                        'carbs_g': macro_targets.carbs_g * percentage,
                        'fat_g': macro_targets.fat_g * percentage
                    }
                    
                    # Get AI suggestions for this meal
                    ai_suggestions = await self.openai_service.generate_meal_suggestions(
                        user_profile=user_profile,
                        nutrition_targets=meal_targets,
                        dietary_restrictions=[restriction.type for restriction in user.dietary_restrictions],
                        meal_type=meal_type
                    )
                    
                    if ai_suggestions:
                        meal_foods = []
                        for suggestion in ai_suggestions[:1]:  # One suggestion per meal
                            food_suggestion = FoodSuggestion(
                                fdc_id=0,
                                food_name=suggestion.get('name', 'Unknown'),
                                serving_size=1.0,
                                serving_unit="serving",
                                calories=suggestion.get('estimated_nutrition', {}).get('calories', 0),
                                protein_g=suggestion.get('estimated_nutrition', {}).get('protein_g', 0),
                                carbs_g=suggestion.get('estimated_nutrition', {}).get('carbs_g', 0),
                                fat_g=suggestion.get('estimated_nutrition', {}).get('fat_g', 0),
                                reason=suggestion.get('rationale', ''),
                                meal_type=meal_type,
                                priority_score=0.8,
                                nutritional_benefits=[],
                                matches_dietary_restrictions=True,
                                allergen_warnings=[]
                            )
                            meal_foods.append(food_suggestion)
                        daily_meals[meal_type] = meal_foods
                
                if daily_meals:
                    meal_plan = MealPlan(
                        date=datetime.now(),
                        meals=daily_meals,
                        total_calories=macro_targets.calories,
                        total_protein_g=macro_targets.protein_g,
                        total_carbs_g=macro_targets.carbs_g,
                        total_fat_g=macro_targets.fat_g,
                        total_fiber_g=macro_targets.fiber_g,
                        plan_type="daily",
                        difficulty_level="easy",
                        prep_time_minutes=45,
                        cost_estimate=25.0
                    )
                    
                    recommendation = Recommendation(
                        user_id=str(user.id),
                        recommendation_type=RecommendationType.MEAL_PLAN,
                        title="Personalized Daily Meal Plan",
                        description="A complete meal plan designed to meet your nutritional goals and preferences",
                        confidence_level=ConfidenceLevel.MEDIUM,
                        meal_plan=meal_plan,
                        model_version="1.0",
                        model_confidence=0.70,
                        features_used=["nutrition_targets", "user_preferences", "meal_distribution"],
                        user_goals=[user.primary_goal] if user.primary_goal else [],
                        health_conditions=[condition.name for condition in user.health_conditions],
                        dietary_restrictions=[restriction.type for restriction in user.dietary_restrictions],
                        priority=RecommendationPriority.LOW.value,
                        expected_impact="high",
                        implementation_difficulty="medium",
                        time_horizon="short_term"
                    )
                    recommendations.append(recommendation)
        
        except Exception as e:
            logger.error(f"Error generating meal plan recommendations: {e}")

        return recommendations

    async def _generate_health_optimization_recommendations(
        self,
        user: User,
        current_intake: Dict[str, float]
    ) -> List[Recommendation]:
        """Generate health optimization recommendations based on conditions."""
        recommendations = []

        try:
            for condition in user.health_conditions:
                condition_name = condition.name.lower()

                if 'diabetes' in condition_name:
                    recommendations.extend(await self._diabetes_recommendations(user, current_intake))
                elif 'hypertension' in condition_name or 'blood pressure' in condition_name:
                    recommendations.extend(await self._hypertension_recommendations(user, current_intake))
                elif 'heart' in condition_name or 'cardiovascular' in condition_name:
                    recommendations.extend(await self._heart_health_recommendations(user, current_intake))
                elif 'anemia' in condition_name:
                    recommendations.extend(await self._anemia_recommendations(user, current_intake))
                elif 'osteoporosis' in condition_name:
                    recommendations.extend(await self._bone_health_recommendations(user, current_intake))

        except Exception as e:
            logger.error(f"Error generating health optimization recommendations: {e}")

        return recommendations

    async def _diabetes_recommendations(self, user: User, current_intake: Dict[str, float]) -> List[Recommendation]:
        """Generate diabetes-specific recommendations."""
        recommendations = []

        # Check carb intake and fiber
        carbs = current_intake.get('carbs_g', 0)
        fiber = current_intake.get('fiber_g', 0)

        adjustments = []

        if fiber < 25:  # Low fiber
            adjustments.append(NutrientAdjustment(
                nutrient_name="fiber_g",
                current_intake=fiber,
                recommended_intake=30,
                adjustment_amount=30 - fiber,
                adjustment_direction="increase",
                unit="g",
                reason="Higher fiber intake helps regulate blood sugar levels",
                health_impact="Improved glucose control and insulin sensitivity",
                food_sources=["whole grains", "legumes", "vegetables", "fruits with skin"],
                supplement_suggestion="Consider a fiber supplement if dietary intake is insufficient"
            ))

        if adjustments:
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.HEALTH_OPTIMIZATION,
                title="Diabetes Management Nutrition",
                description="Optimize your nutrition to better manage blood sugar levels",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=adjustments,
                model_version="1.0",
                model_confidence=0.90,
                features_used=["health_conditions", "current_intake", "clinical_guidelines"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=["diabetes"],
                priority=RecommendationPriority.HIGH.value,
                expected_impact="high",
                implementation_difficulty="medium",
                time_horizon="long_term"
            )
            recommendations.append(recommendation)

        return recommendations

    async def _hypertension_recommendations(self, user: User, current_intake: Dict[str, float]) -> List[Recommendation]:
        """Generate hypertension-specific recommendations."""
        recommendations = []

        sodium = current_intake.get('sodium_mg', 0)
        potassium = current_intake.get('potassium_mg', 0)

        adjustments = []

        if sodium > 2300:  # High sodium
            adjustments.append(NutrientAdjustment(
                nutrient_name="sodium_mg",
                current_intake=sodium,
                recommended_intake=1500,
                adjustment_amount=sodium - 1500,
                adjustment_direction="decrease",
                unit="mg",
                reason="Reducing sodium intake helps lower blood pressure",
                health_impact="Reduced risk of cardiovascular events",
                food_sources=["fresh fruits", "vegetables", "unsalted nuts", "herbs and spices"],
                supplement_suggestion="Focus on whole foods rather than supplements"
            ))

        if potassium < 3500:  # Low potassium
            adjustments.append(NutrientAdjustment(
                nutrient_name="potassium_mg",
                current_intake=potassium,
                recommended_intake=4700,
                adjustment_amount=4700 - potassium,
                adjustment_direction="increase",
                unit="mg",
                reason="Adequate potassium helps counteract sodium's effects on blood pressure",
                health_impact="Better blood pressure control",
                food_sources=["bananas", "oranges", "potatoes", "spinach", "beans"],
                supplement_suggestion="Consult healthcare provider before potassium supplements"
            ))

        if adjustments:
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.HEALTH_OPTIMIZATION,
                title="Blood Pressure Management",
                description="Nutritional strategies to help manage blood pressure",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=adjustments,
                model_version="1.0",
                model_confidence=0.88,
                features_used=["health_conditions", "current_intake", "clinical_guidelines"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=["hypertension"],
                priority=RecommendationPriority.HIGH.value,
                expected_impact="high",
                implementation_difficulty="medium",
                time_horizon="long_term"
            )
            recommendations.append(recommendation)

        return recommendations

    async def _heart_health_recommendations(self, user: User, current_intake: Dict[str, float]) -> List[Recommendation]:
        """Generate heart health recommendations."""
        recommendations = []

        # Focus on omega-3, fiber, and antioxidants
        fiber = current_intake.get('fiber_g', 0)

        adjustments = []

        if fiber < 25:
            adjustments.append(NutrientAdjustment(
                nutrient_name="fiber_g",
                current_intake=fiber,
                recommended_intake=30,
                adjustment_amount=30 - fiber,
                adjustment_direction="increase",
                unit="g",
                reason="Soluble fiber helps reduce cholesterol levels",
                health_impact="Improved cardiovascular health and cholesterol profile",
                food_sources=["oats", "beans", "apples", "barley", "psyllium"],
                supplement_suggestion="Consider psyllium husk supplement"
            ))

        if adjustments:
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.HEALTH_OPTIMIZATION,
                title="Heart Health Optimization",
                description="Nutrition recommendations to support cardiovascular health",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=adjustments,
                model_version="1.0",
                model_confidence=0.85,
                features_used=["health_conditions", "current_intake", "clinical_guidelines"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=["heart_disease"],
                priority=RecommendationPriority.HIGH.value,
                expected_impact="high",
                implementation_difficulty="medium",
                time_horizon="long_term"
            )
            recommendations.append(recommendation)

        return recommendations

    async def _anemia_recommendations(self, user: User, current_intake: Dict[str, float]) -> List[Recommendation]:
        """Generate anemia-specific recommendations."""
        recommendations = []

        iron = current_intake.get('iron_mg', 0)
        vitamin_c = current_intake.get('vitamin_c_mg', 0)

        adjustments = []

        if iron < 15:  # Low iron
            adjustments.append(NutrientAdjustment(
                nutrient_name="iron_mg",
                current_intake=iron,
                recommended_intake=18,
                adjustment_amount=18 - iron,
                adjustment_direction="increase",
                unit="mg",
                reason="Adequate iron intake is essential for red blood cell production",
                health_impact="Improved energy levels and oxygen transport",
                food_sources=["lean red meat", "spinach", "lentils", "fortified cereals"],
                supplement_suggestion="Consider iron supplement with healthcare provider guidance"
            ))

        if vitamin_c < 75:  # Low vitamin C (helps iron absorption)
            adjustments.append(NutrientAdjustment(
                nutrient_name="vitamin_c_mg",
                current_intake=vitamin_c,
                recommended_intake=90,
                adjustment_amount=90 - vitamin_c,
                adjustment_direction="increase",
                unit="mg",
                reason="Vitamin C enhances iron absorption",
                health_impact="Better iron utilization and absorption",
                food_sources=["citrus fruits", "bell peppers", "strawberries", "broccoli"],
                supplement_suggestion="Vitamin C supplement can be taken with iron-rich meals"
            ))

        if adjustments:
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.HEALTH_OPTIMIZATION,
                title="Anemia Management Nutrition",
                description="Nutritional support for managing anemia and improving iron status",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=adjustments,
                model_version="1.0",
                model_confidence=0.92,
                features_used=["health_conditions", "current_intake", "clinical_guidelines"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=["anemia"],
                priority=RecommendationPriority.HIGH.value,
                expected_impact="high",
                implementation_difficulty="easy",
                time_horizon="medium_term"
            )
            recommendations.append(recommendation)

        return recommendations

    async def _bone_health_recommendations(self, user: User, current_intake: Dict[str, float]) -> List[Recommendation]:
        """Generate bone health recommendations."""
        recommendations = []

        calcium = current_intake.get('calcium_mg', 0)
        vitamin_d = current_intake.get('vitamin_d_mcg', 0)

        adjustments = []

        if calcium < 1000:  # Low calcium
            adjustments.append(NutrientAdjustment(
                nutrient_name="calcium_mg",
                current_intake=calcium,
                recommended_intake=1200,
                adjustment_amount=1200 - calcium,
                adjustment_direction="increase",
                unit="mg",
                reason="Adequate calcium is essential for bone strength and density",
                health_impact="Reduced risk of fractures and bone loss",
                food_sources=["dairy products", "leafy greens", "sardines", "almonds"],
                supplement_suggestion="Calcium citrate supplement if dietary intake is insufficient"
            ))

        if vitamin_d < 15:  # Low vitamin D
            adjustments.append(NutrientAdjustment(
                nutrient_name="vitamin_d_mcg",
                current_intake=vitamin_d,
                recommended_intake=20,
                adjustment_amount=20 - vitamin_d,
                adjustment_direction="increase",
                unit="mcg",
                reason="Vitamin D is crucial for calcium absorption and bone health",
                health_impact="Better calcium utilization and bone mineralization",
                food_sources=["fatty fish", "fortified milk", "egg yolks", "mushrooms"],
                supplement_suggestion="Vitamin D3 supplement recommended, especially in winter"
            ))

        if adjustments:
            recommendation = Recommendation(
                user_id=str(user.id),
                recommendation_type=RecommendationType.HEALTH_OPTIMIZATION,
                title="Bone Health Support",
                description="Nutritional strategies to support bone health and prevent osteoporosis",
                confidence_level=ConfidenceLevel.HIGH,
                nutrient_adjustments=adjustments,
                model_version="1.0",
                model_confidence=0.87,
                features_used=["health_conditions", "current_intake", "clinical_guidelines"],
                user_goals=[user.primary_goal] if user.primary_goal else [],
                health_conditions=["osteoporosis"],
                priority=RecommendationPriority.HIGH.value,
                expected_impact="high",
                implementation_difficulty="easy",
                time_horizon="long_term"
            )
            recommendations.append(recommendation)

        return recommendations

    def _get_nutrient_gap_reason(self, nutrient: str, ratio: float, user: User) -> str:
        """Get explanation for nutrient gap."""
        if ratio < 0.5:
            severity = "critically low"
        elif ratio < 0.8:
            severity = "below target"
        else:
            severity = "above recommended levels"

        nutrient_benefits = {
            'protein_g': "muscle maintenance and repair",
            'fiber_g': "digestive health and blood sugar control",
            'calories': "energy balance and metabolic function",
            'carbs_g': "energy production and brain function",
            'fat_g': "hormone production and nutrient absorption"
        }

        benefit = nutrient_benefits.get(nutrient, "overall health")
        return f"Your {nutrient.replace('_', ' ')} intake is {severity}, which may impact {benefit}."

    def _get_health_impact(self, nutrient: str, severity: str) -> str:
        """Get health impact description for nutrient deficiency/excess."""
        impacts = {
            'protein_g': {
                'critical': "Risk of muscle loss and impaired immune function",
                'high': "Reduced muscle protein synthesis and recovery",
                'excess': "Potential kidney strain and dehydration"
            },
            'fiber_g': {
                'critical': "Digestive issues and blood sugar instability",
                'high': "Suboptimal digestive health and satiety",
                'excess': "Potential digestive discomfort and bloating"
            },
            'calories': {
                'critical': "Risk of malnutrition and metabolic slowdown",
                'high': "Energy deficiency and potential muscle loss",
                'excess': "Weight gain and metabolic dysfunction"
            }
        }

        return impacts.get(nutrient, {}).get(severity, "May affect overall health and wellness")

    def _get_food_sources_for_nutrient(self, nutrient: str) -> List[str]:
        """Get food sources rich in specific nutrient."""
        sources = {
            'protein_g': ["lean meats", "fish", "eggs", "legumes", "dairy", "nuts"],
            'fiber_g': ["whole grains", "vegetables", "fruits", "legumes", "nuts"],
            'calories': ["healthy fats", "whole grains", "lean proteins", "fruits"],
            'carbs_g': ["whole grains", "fruits", "vegetables", "legumes"],
            'fat_g': ["avocados", "nuts", "olive oil", "fatty fish", "seeds"],
            'iron_mg': ["red meat", "spinach", "lentils", "fortified cereals"],
            'calcium_mg': ["dairy products", "leafy greens", "sardines", "almonds"],
            'vitamin_c_mg': ["citrus fruits", "bell peppers", "strawberries", "broccoli"],
            'vitamin_d_mcg': ["fatty fish", "fortified milk", "egg yolks", "mushrooms"]
        }

        return sources.get(nutrient, ["varied whole foods"])

    def _determine_next_meal(self) -> str:
        """Determine the next appropriate meal based on time of day."""
        current_hour = datetime.now().hour

        if 5 <= current_hour < 11:
            return "breakfast"
        elif 11 <= current_hour < 15:
            return "lunch"
        elif 15 <= current_hour < 18:
            return "snack"
        else:
            return "dinner"

    def _check_allergens(self, suggestion: Dict[str, Any], user_allergies: List[str]) -> List[str]:
        """Check for potential allergens in food suggestion."""
        warnings = []

        suggestion_text = suggestion.get('name', '').lower() + ' ' + ' '.join(
            ingredient.get('name', '').lower()
            for ingredient in suggestion.get('ingredients', [])
        )

        common_allergens = {
            'milk': ['milk', 'dairy', 'cheese', 'butter', 'cream'],
            'eggs': ['egg', 'eggs'],
            'fish': ['fish', 'salmon', 'tuna', 'cod'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'shellfish'],
            'tree nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio'],
            'peanuts': ['peanut', 'peanuts'],
            'wheat': ['wheat', 'flour', 'bread', 'pasta'],
            'soy': ['soy', 'tofu', 'soybean', 'edamame']
        }

        for allergy in user_allergies:
            allergy_lower = allergy.lower()
            for allergen_group, keywords in common_allergens.items():
                if allergy_lower in allergen_group or any(keyword in allergy_lower for keyword in keywords):
                    if any(keyword in suggestion_text for keyword in keywords):
                        warnings.append(f"May contain {allergen_group}")

        return warnings

    async def get_recommendation_by_id(self, recommendation_id: str, user_id: str) -> Optional[Recommendation]:
        """Get a specific recommendation by ID."""
        try:
            recommendation = await Recommendation.get(recommendation_id)
            if recommendation and recommendation.user_id == user_id:
                return recommendation
            return None
        except Exception as e:
            logger.error(f"Error getting recommendation {recommendation_id}: {e}")
            return None

    async def update_recommendation_feedback(
        self,
        recommendation_id: str,
        user_id: str,
        is_accepted: bool,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """Update recommendation with user feedback."""
        try:
            recommendation = await self.get_recommendation_by_id(recommendation_id, user_id)
            if not recommendation:
                return False

            recommendation.is_viewed = True
            recommendation.is_accepted = is_accepted
            if rating:
                recommendation.user_rating = rating
            if feedback:
                recommendation.user_feedback = feedback

            await recommendation.save()
            logger.info(f"Updated recommendation {recommendation_id} with feedback")
            return True

        except Exception as e:
            logger.error(f"Error updating recommendation feedback: {e}")
            return False

    async def get_user_recommendations(
        self,
        user_id: str,
        active_only: bool = True,
        limit: int = 10
    ) -> List[Recommendation]:
        """Get recommendations for a user."""
        try:
            query = {"user_id": user_id}
            if active_only:
                query["is_active"] = True

            recommendations = await Recommendation.find(query).sort([
                ("priority", 1),
                ("created_at", -1)
            ]).limit(limit).to_list()

            return recommendations

        except Exception as e:
            logger.error(f"Error getting user recommendations: {e}")
            return []

    async def deactivate_old_recommendations(self, user_id: str, days_old: int = 7):
        """Deactivate recommendations older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            await Recommendation.find({
                "user_id": user_id,
                "created_at": {"$lt": cutoff_date},
                "is_active": True
            }).update({"$set": {"is_active": False}})

            logger.info(f"Deactivated old recommendations for user {user_id}")

        except Exception as e:
            logger.error(f"Error deactivating old recommendations: {e}")

    async def get_recommendation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get recommendation statistics for a user."""
        try:
            total_recommendations = await Recommendation.find({"user_id": user_id}).count()
            active_recommendations = await Recommendation.find({
                "user_id": user_id,
                "is_active": True
            }).count()
            accepted_recommendations = await Recommendation.find({
                "user_id": user_id,
                "is_accepted": True
            }).count()

            # Get average rating
            rated_recommendations = await Recommendation.find({
                "user_id": user_id,
                "user_rating": {"$exists": True, "$ne": None}
            }).to_list()

            avg_rating = None
            if rated_recommendations:
                avg_rating = sum(r.user_rating for r in rated_recommendations) / len(rated_recommendations)

            # Get recommendations by type
            recommendations_by_type = {}
            all_recommendations = await Recommendation.find({"user_id": user_id}).to_list()
            for rec in all_recommendations:
                rec_type = rec.recommendation_type
                recommendations_by_type[rec_type] = recommendations_by_type.get(rec_type, 0) + 1

            # Get recent recommendations
            recent_recommendations = await Recommendation.find({
                "user_id": user_id
            }).sort([("created_at", -1)]).limit(5).to_list()

            return {
                "total_recommendations": total_recommendations,
                "active_recommendations": active_recommendations,
                "accepted_recommendations": accepted_recommendations,
                "average_rating": avg_rating,
                "recommendations_by_type": recommendations_by_type,
                "recent_recommendations": recent_recommendations
            }

        except Exception as e:
            logger.error(f"Error getting recommendation stats: {e}")
            return {
                "total_recommendations": 0,
                "active_recommendations": 0,
                "accepted_recommendations": 0,
                "average_rating": None,
                "recommendations_by_type": {},
                "recent_recommendations": []
            }
