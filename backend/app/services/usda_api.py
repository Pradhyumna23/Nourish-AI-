"""
USDA FoodData Central API integration service.
"""

import httpx
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime

from app.core.config import settings
from app.models.food import Food, NutrientInfo, FoodPortion


class USDAApiService:
    """Service for interacting with USDA FoodData Central API."""
    
    def __init__(self):
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.api_key = settings.USDA_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_foods(
        self, 
        query: str, 
        page_size: int = 20, 
        page_number: int = 1,
        data_type: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for foods using USDA FoodData Central API.
        
        Args:
            query: Search query string
            page_size: Number of results per page (max 200)
            page_number: Page number (1-based)
            data_type: List of data types to include (e.g., ['Foundation', 'SR Legacy'])
        
        Returns:
            Dictionary containing search results
        """
        try:
            url = f"{self.base_url}/foods/search"
            
            params = {
                "api_key": self.api_key,
                "query": query,
                "pageSize": min(page_size, 200),
                "pageNumber": page_number,
                "sortBy": "relevance",
                "sortOrder": "desc"
            }
            
            if data_type:
                params["dataType"] = data_type
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"USDA API search successful: {query} - {data.get('totalHits', 0)} results")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"USDA API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"USDA API search error: {e}")
            raise
    
    async def get_food_details(self, fdc_id: int, nutrients: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Get detailed food information by FDC ID.
        
        Args:
            fdc_id: Food Data Central ID
            nutrients: List of nutrient IDs to include (optional)
        
        Returns:
            Dictionary containing food details
        """
        try:
            url = f"{self.base_url}/food/{fdc_id}"
            
            params = {
                "api_key": self.api_key,
                "format": "full"
            }
            
            if nutrients:
                params["nutrients"] = nutrients
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"USDA API food details successful: FDC ID {fdc_id}")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"USDA API HTTP error for FDC ID {fdc_id}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"USDA API food details error for FDC ID {fdc_id}: {e}")
            raise
    
    async def get_multiple_foods(self, fdc_ids: List[int]) -> Dict[str, Any]:
        """
        Get details for multiple foods by FDC IDs.
        
        Args:
            fdc_ids: List of Food Data Central IDs (max 20)
        
        Returns:
            Dictionary containing multiple food details
        """
        try:
            url = f"{self.base_url}/foods"
            
            # Limit to 20 IDs as per API constraints
            fdc_ids = fdc_ids[:20]
            
            payload = {
                "fdcIds": fdc_ids,
                "format": "full",
                "nutrients": []  # Include all nutrients
            }
            
            params = {"api_key": self.api_key}
            
            response = await self.client.post(url, json=payload, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"USDA API multiple foods successful: {len(fdc_ids)} foods")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"USDA API HTTP error for multiple foods: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"USDA API multiple foods error: {e}")
            raise
    
    def _parse_food_data(self, food_data: Dict[str, Any]) -> Food:
        """
        Parse USDA API food data into our Food model.
        
        Args:
            food_data: Raw food data from USDA API
        
        Returns:
            Food model instance
        """
        try:
            # Parse nutrients
            nutrients = []
            for nutrient in food_data.get("foodNutrients", []):
                nutrient_info = NutrientInfo(
                    nutrient_id=nutrient.get("nutrient", {}).get("id"),
                    name=nutrient.get("nutrient", {}).get("name", ""),
                    unit=nutrient.get("nutrient", {}).get("unitName", ""),
                    amount=nutrient.get("amount", 0.0),
                    derivation_code=nutrient.get("dataPoints", 0),
                    derivation_description=nutrient.get("derivationDescription")
                )
                nutrients.append(nutrient_info)
            
            # Parse food portions
            portions = []
            for portion in food_data.get("foodPortions", []):
                food_portion = FoodPortion(
                    id=portion.get("id"),
                    amount=portion.get("amount", 0.0),
                    unit=portion.get("modifier", ""),
                    modifier=portion.get("portionDescription", ""),
                    gram_weight=portion.get("gramWeight", 0.0),
                    sequence_number=portion.get("sequenceNumber")
                )
                portions.append(food_portion)
            
            # Create Food instance
            food = Food(
                fdc_id=food_data.get("fdcId"),
                data_type=food_data.get("dataType", ""),
                description=food_data.get("description", ""),
                food_code=food_data.get("foodCode"),
                publication_date=self._parse_date(food_data.get("publicationDate")),
                brand_owner=food_data.get("brandOwner"),
                brand_name=food_data.get("brandName"),
                subbrand_name=food_data.get("subbrandName"),
                gtin_upc=food_data.get("gtinUpc"),
                nutrients=nutrients,
                food_portions=portions,
                food_category=food_data.get("foodCategory"),
                food_category_id=food_data.get("foodCategoryId"),
                ingredients=food_data.get("ingredients"),
                serving_size=food_data.get("servingSize"),
                serving_size_unit=food_data.get("servingSizeUnit"),
                household_serving_fulltext=food_data.get("householdServingFullText")
            )
            
            return food
            
        except Exception as e:
            logger.error(f"Error parsing food data: {e}")
            raise
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string from USDA API."""
        if not date_string:
            return None
        
        try:
            # USDA API typically returns dates in format: "2019-04-01"
            return datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            try:
                # Try alternative format
                return datetime.strptime(date_string, "%m/%d/%Y")
            except ValueError:
                logger.warning(f"Could not parse date: {date_string}")
                return None
    
    async def save_food_to_database(self, food_data: Dict[str, Any]) -> Food:
        """
        Parse and save food data to database.
        
        Args:
            food_data: Raw food data from USDA API
        
        Returns:
            Saved Food model instance
        """
        try:
            # Check if food already exists
            existing_food = await Food.find_one({"fdc_id": food_data.get("fdcId")})
            if existing_food:
                logger.info(f"Food already exists in database: FDC ID {food_data.get('fdcId')}")
                return existing_food
            
            # Parse and save new food
            food = self._parse_food_data(food_data)
            await food.insert()
            
            logger.info(f"Food saved to database: FDC ID {food.fdc_id} - {food.description}")
            return food
            
        except Exception as e:
            logger.error(f"Error saving food to database: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
