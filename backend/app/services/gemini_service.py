"""
Gemini AI service for food parsing and AI-powered features.
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
from loguru import logger
import json
import os

from app.core.config import settings


class GeminiService:
    """Service for Google Gemini AI interactions."""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def parse_food_description(self, description: str) -> Dict[str, Any]:
        """
        Parse natural language food description into structured data.
        
        Args:
            description: Natural language description of food (e.g., "2 slices of whole wheat bread")
        
        Returns:
            Dictionary with parsed food information
        """
        try:
            prompt = f"""
            Parse the following food description into structured data. Extract:
            1. Food name/type
            2. Quantity (number)
            3. Unit of measurement
            4. Any modifiers (brand, preparation method, etc.)
            
            Food description: "{description}"
            
            Return the result as JSON with the following structure:
            {{
                "food_name": "extracted food name",
                "quantity": number,
                "unit": "unit of measurement",
                "modifiers": ["list", "of", "modifiers"],
                "search_terms": ["alternative", "search", "terms"],
                "confidence": 0.0-1.0
            }}
            
            If you cannot parse the description, set confidence to 0.
            Always respond with valid JSON only, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Try to parse JSON response
            try:
                parsed_data = json.loads(content)
                logger.info(f"Successfully parsed food description: {description}")
                return parsed_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response from Gemini: {content}")
                return self._fallback_parse(description)
                
        except Exception as e:
            logger.error(f"Gemini food parsing error: {e}")
            return self._fallback_parse(description)
    
    def _fallback_parse(self, description: str) -> Dict[str, Any]:
        """Fallback parsing when Gemini fails."""
        return {
            "food_name": description,
            "quantity": 1.0,
            "unit": "serving",
            "modifiers": [],
            "search_terms": [description],
            "confidence": 0.3
        }
    
    async def generate_meal_suggestions(
        self, 
        user_profile: Dict[str, Any], 
        nutrition_targets: Dict[str, float],
        dietary_restrictions: List[str] = None,
        meal_type: str = "lunch"
    ) -> List[Dict[str, Any]]:
        """
        Generate meal suggestions based on user profile and nutrition targets.
        
        Args:
            user_profile: User's health and preference profile
            nutrition_targets: Target nutrition values
            dietary_restrictions: List of dietary restrictions
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
        
        Returns:
            List of meal suggestions
        """
        try:
            restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
            
            prompt = f"""
            Generate 3 healthy {meal_type} meal suggestions for a user with the following profile:
            
            User Profile:
            - Age: {user_profile.get('age', 'unknown')}
            - Gender: {user_profile.get('gender', 'unknown')}
            - Activity Level: {user_profile.get('activity_level', 'unknown')}
            - Primary Goal: {user_profile.get('primary_goal', 'unknown')}
            - Health Conditions: {user_profile.get('health_conditions', [])}
            
            Nutrition Targets for this meal:
            - Calories: {nutrition_targets.get('calories', 500)}
            - Protein: {nutrition_targets.get('protein_g', 20)}g
            - Carbs: {nutrition_targets.get('carbs_g', 50)}g
            - Fat: {nutrition_targets.get('fat_g', 20)}g
            
            Dietary Restrictions: {restrictions_text}
            
            For each suggestion, provide:
            1. Meal name
            2. List of ingredients with approximate quantities
            3. Brief preparation instructions
            4. Estimated nutrition values
            5. Why this meal fits the user's profile
            
            Return as JSON array with this structure:
            [
                {{
                    "name": "Meal Name",
                    "ingredients": [
                        {{"name": "ingredient", "quantity": "amount", "unit": "unit"}},
                        ...
                    ],
                    "instructions": "Brief preparation steps",
                    "estimated_nutrition": {{
                        "calories": number,
                        "protein_g": number,
                        "carbs_g": number,
                        "fat_g": number
                    }},
                    "rationale": "Why this meal is good for the user",
                    "prep_time_minutes": number,
                    "difficulty": "easy|medium|hard"
                }},
                ...
            ]
            
            Respond with valid JSON only, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            try:
                suggestions = json.loads(content)
                logger.info(f"Generated {len(suggestions)} meal suggestions for {meal_type}")
                return suggestions
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse meal suggestions JSON: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Gemini meal suggestion error: {e}")
            return []
    
    async def analyze_nutrition_gaps(
        self,
        current_intake: Dict[str, float],
        target_intake: Dict[str, float],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze nutrition gaps and provide recommendations.
        
        Args:
            current_intake: Current daily nutrition intake
            target_intake: Target nutrition values
            user_profile: User's profile information
        
        Returns:
            Analysis with recommendations
        """
        try:
            prompt = f"""
            Analyze the nutrition gaps for a user and provide recommendations:
            
            Current Daily Intake:
            {json.dumps(current_intake, indent=2)}
            
            Target Daily Intake:
            {json.dumps(target_intake, indent=2)}
            
            User Profile:
            - Age: {user_profile.get('age', 'unknown')}
            - Gender: {user_profile.get('gender', 'unknown')}
            - Activity Level: {user_profile.get('activity_level', 'unknown')}
            - Primary Goal: {user_profile.get('primary_goal', 'unknown')}
            - Health Conditions: {user_profile.get('health_conditions', [])}
            
            Provide analysis and recommendations in JSON format:
            {{
                "gaps": [
                    {{
                        "nutrient": "nutrient name",
                        "current": number,
                        "target": number,
                        "gap": number,
                        "severity": "low|medium|high",
                        "impact": "description of health impact"
                    }},
                    ...
                ],
                "recommendations": [
                    {{
                        "type": "food|supplement|lifestyle",
                        "description": "specific recommendation",
                        "foods": ["list", "of", "recommended", "foods"],
                        "priority": "low|medium|high"
                    }},
                    ...
                ],
                "overall_assessment": "summary of nutrition status",
                "next_steps": ["actionable", "steps"]
            }}
            
            Respond with valid JSON only, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            try:
                analysis = json.loads(content)
                logger.info("Generated nutrition gap analysis")
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse nutrition analysis JSON: {content}")
                return {"gaps": [], "recommendations": [], "overall_assessment": "Analysis unavailable", "next_steps": []}
                
        except Exception as e:
            logger.error(f"Gemini nutrition analysis error: {e}")
            return {"gaps": [], "recommendations": [], "overall_assessment": "Analysis unavailable", "next_steps": []}
    
    async def generate_shopping_list(
        self,
        meal_plan: List[Dict[str, Any]],
        dietary_restrictions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a shopping list from a meal plan.
        
        Args:
            meal_plan: List of planned meals
            dietary_restrictions: User's dietary restrictions
        
        Returns:
            Organized shopping list
        """
        try:
            restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
            
            prompt = f"""
            Generate an organized shopping list from this meal plan:
            
            Meal Plan:
            {json.dumps(meal_plan, indent=2)}
            
            Dietary Restrictions: {restrictions_text}
            
            Organize the shopping list by grocery store sections and include:
            1. Consolidated quantities (combine duplicate ingredients)
            2. Suggested brands or alternatives for dietary restrictions
            3. Estimated total cost range
            4. Storage tips for perishables
            
            Return as JSON:
            {{
                "sections": {{
                    "produce": [
                        {{"item": "item name", "quantity": "amount", "unit": "unit", "notes": "optional notes"}},
                        ...
                    ],
                    "dairy": [...],
                    "meat_seafood": [...],
                    "pantry": [...],
                    "frozen": [...],
                    "other": [...]
                }},
                "estimated_cost": {{"min": number, "max": number, "currency": "USD"}},
                "storage_tips": ["tip1", "tip2", ...],
                "meal_count": number,
                "total_items": number
            }}
            
            Respond with valid JSON only, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            try:
                shopping_list = json.loads(content)
                logger.info("Generated shopping list")
                return shopping_list
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse shopping list JSON: {content}")
                return {"sections": {}, "estimated_cost": {"min": 0, "max": 0, "currency": "USD"}, "storage_tips": [], "meal_count": 0, "total_items": 0}
                
        except Exception as e:
            logger.error(f"Gemini shopping list error: {e}")
            return {"sections": {}, "estimated_cost": {"min": 0, "max": 0, "currency": "USD"}, "storage_tips": [], "meal_count": 0, "total_items": 0}
