"""
Food service for managing food data and operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from loguru import logger
from fastapi import HTTPException, status

from app.models.food import Food, FoodItem, FoodSearch, NutritionSummary
from app.models.user import User
from app.services.usda_api import USDAApiService


class FoodService:
    """Service for food-related operations."""
    
    def __init__(self):
        self.usda_service = USDAApiService()
    
    async def search_foods(
        self, 
        search_params: FoodSearch, 
        user: User
    ) -> Dict[str, Any]:
        """
        Search for foods using USDA API and local database.
        
        Args:
            search_params: Search parameters
            user: Current user
        
        Returns:
            Search results with foods
        """
        try:
            # First, search local database
            local_foods = await self._search_local_foods(search_params.query, search_params.page_size)
            
            # If we don't have enough results, search USDA API
            if len(local_foods) < search_params.page_size:
                usda_results = await self.usda_service.search_foods(
                    query=search_params.query,
                    page_size=search_params.page_size,
                    page_number=search_params.page_number,
                    data_type=search_params.data_type
                )
                
                # Process and save new foods from USDA
                for food_data in usda_results.get("foods", []):
                    try:
                        await self.usda_service.save_food_to_database(food_data)
                    except Exception as e:
                        logger.warning(f"Failed to save food {food_data.get('fdcId')}: {e}")
                
                # Search local database again to get updated results
                local_foods = await self._search_local_foods(search_params.query, search_params.page_size)
            
            return {
                "foods": local_foods,
                "totalHits": len(local_foods),
                "currentPage": search_params.page_number,
                "totalPages": 1
            }
            
        except Exception as e:
            logger.error(f"Food search error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Food search failed: {str(e)}"
            )
    
    async def _search_local_foods(self, query: str, limit: int = 20) -> List[Food]:
        """Search foods in local database."""
        try:
            # Use text search on description field
            foods = await Food.find(
                {"$text": {"$search": query}}
            ).limit(limit).to_list()
            
            return foods
            
        except Exception as e:
            logger.error(f"Local food search error: {e}")
            return []
    
    async def get_food_by_fdc_id(self, fdc_id: int) -> Optional[Food]:
        """
        Get food by FDC ID from local database or USDA API.
        
        Args:
            fdc_id: Food Data Central ID
        
        Returns:
            Food instance or None
        """
        try:
            # First check local database
            food = await Food.find_one({"fdc_id": fdc_id})
            
            if not food:
                # Fetch from USDA API and save
                food_data = await self.usda_service.get_food_details(fdc_id)
                food = await self.usda_service.save_food_to_database(food_data)
            
            return food
            
        except Exception as e:
            logger.error(f"Error getting food by FDC ID {fdc_id}: {e}")
            return None
    
    async def log_food_item(
        self, 
        user_id: str, 
        fdc_id: int, 
        date: datetime, 
        meal_type: str, 
        quantity: float, 
        unit: str,
        notes: Optional[str] = None
    ) -> FoodItem:
        """
        Log a food item for a user.
        
        Args:
            user_id: User ID
            fdc_id: Food Data Central ID
            date: Date of consumption
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            quantity: Quantity consumed
            unit: Unit of measurement
            notes: Optional notes
        
        Returns:
            Created FoodItem
        """
        try:
            # Get food details
            food = await self.get_food_by_fdc_id(fdc_id)
            if not food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food with FDC ID {fdc_id} not found"
                )
            
            # Calculate gram weight
            gram_weight = self._calculate_gram_weight(food, quantity, unit)
            
            # Calculate nutrition for this serving
            nutrition = self._calculate_nutrition_for_serving(food, gram_weight)
            
            # Create food item
            food_item = FoodItem(
                user_id=user_id,
                food_id=str(food.id),
                fdc_id=fdc_id,
                date=date,
                meal_type=meal_type,
                quantity=quantity,
                unit=unit,
                gram_weight=gram_weight,
                calories=nutrition.get("calories"),
                protein_g=nutrition.get("protein_g"),
                carbs_g=nutrition.get("carbs_g"),
                fat_g=nutrition.get("fat_g"),
                fiber_g=nutrition.get("fiber_g"),
                sugar_g=nutrition.get("sugar_g"),
                sodium_mg=nutrition.get("sodium_mg"),
                nutrients=nutrition.get("nutrients", {}),
                notes=notes
            )
            
            await food_item.insert()
            logger.info(f"Food item logged: User {user_id}, Food {fdc_id}")
            
            return food_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error logging food item: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to log food item: {str(e)}"
            )
    
    def _calculate_gram_weight(self, food: Food, quantity: float, unit: str) -> float:
        """Calculate gram weight for a given quantity and unit."""
        try:
            # If unit is already grams
            if unit.lower() in ["g", "gram", "grams"]:
                return quantity
            
            # Look for matching food portion
            for portion in food.food_portions:
                if portion.unit.lower() == unit.lower() or portion.modifier.lower() == unit.lower():
                    return quantity * portion.gram_weight
            
            # Default: assume 100g serving if no portion found
            logger.warning(f"No portion found for unit '{unit}' in food {food.fdc_id}, using 100g default")
            return quantity * 100.0
            
        except Exception as e:
            logger.error(f"Error calculating gram weight: {e}")
            return quantity * 100.0  # Default fallback
    
    def _calculate_nutrition_for_serving(self, food: Food, gram_weight: float) -> Dict[str, Any]:
        """Calculate nutrition values for a specific serving size."""
        try:
            nutrition = {"nutrients": {}}
            
            # Base serving size is typically 100g for USDA data
            base_serving_g = 100.0
            multiplier = gram_weight / base_serving_g
            
            for nutrient in food.nutrients:
                nutrient_amount = nutrient.amount * multiplier
                
                # Map common nutrients to standard fields
                nutrient_name_lower = nutrient.name.lower()
                
                if "energy" in nutrient_name_lower or "calorie" in nutrient_name_lower:
                    nutrition["calories"] = nutrient_amount
                elif "protein" in nutrient_name_lower:
                    nutrition["protein_g"] = nutrient_amount
                elif "carbohydrate" in nutrient_name_lower and "fiber" not in nutrient_name_lower:
                    nutrition["carbs_g"] = nutrient_amount
                elif "total lipid" in nutrient_name_lower or "fat" in nutrient_name_lower:
                    nutrition["fat_g"] = nutrient_amount
                elif "fiber" in nutrient_name_lower:
                    nutrition["fiber_g"] = nutrient_amount
                elif "sugar" in nutrient_name_lower:
                    nutrition["sugar_g"] = nutrient_amount
                elif "sodium" in nutrient_name_lower:
                    nutrition["sodium_mg"] = nutrient_amount
                
                # Store all nutrients
                nutrition["nutrients"][nutrient.name] = nutrient_amount
            
            return nutrition
            
        except Exception as e:
            logger.error(f"Error calculating nutrition: {e}")
            return {"nutrients": {}}
    
    async def get_daily_nutrition_summary(self, user_id: str, target_date: date) -> NutritionSummary:
        """
        Get nutrition summary for a specific date.
        
        Args:
            user_id: User ID
            target_date: Date to get summary for
        
        Returns:
            NutritionSummary
        """
        try:
            # Get all food items for the date
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            food_items = await FoodItem.find({
                "user_id": user_id,
                "date": {"$gte": start_datetime, "$lte": end_datetime}
            }).to_list()
            
            # Calculate totals
            total_calories = sum(item.calories or 0 for item in food_items)
            total_protein_g = sum(item.protein_g or 0 for item in food_items)
            total_carbs_g = sum(item.carbs_g or 0 for item in food_items)
            total_fat_g = sum(item.fat_g or 0 for item in food_items)
            total_fiber_g = sum(item.fiber_g or 0 for item in food_items)
            total_sugar_g = sum(item.sugar_g or 0 for item in food_items)
            total_sodium_mg = sum(item.sodium_mg or 0 for item in food_items)
            
            # Calculate meal breakdown
            meal_breakdown = {}
            for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                meal_items = [item for item in food_items if item.meal_type == meal_type]
                meal_breakdown[meal_type] = {
                    "calories": sum(item.calories or 0 for item in meal_items),
                    "protein_g": sum(item.protein_g or 0 for item in meal_items),
                    "carbs_g": sum(item.carbs_g or 0 for item in meal_items),
                    "fat_g": sum(item.fat_g or 0 for item in meal_items),
                    "fiber_g": sum(item.fiber_g or 0 for item in meal_items)
                }
            
            return NutritionSummary(
                date=start_datetime,
                total_calories=total_calories,
                total_protein_g=total_protein_g,
                total_carbs_g=total_carbs_g,
                total_fat_g=total_fat_g,
                total_fiber_g=total_fiber_g,
                total_sugar_g=total_sugar_g,
                total_sodium_mg=total_sodium_mg,
                meal_breakdown=meal_breakdown,
                food_items_count=len(food_items)
            )
            
        except Exception as e:
            logger.error(f"Error getting daily nutrition summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get nutrition summary: {str(e)}"
            )
    
    async def get_food_log_history(self, user_id: str, days: int = 7) -> List[FoodItem]:
        """
        Get food log history for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            List of FoodItem instances
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            food_items = await FoodItem.find({
                "user_id": user_id,
                "date": {"$gte": start_date}
            }).sort([("date", -1)]).to_list()
            
            return food_items
            
        except Exception as e:
            logger.error(f"Error getting food log history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get food log history: {str(e)}"
            )
