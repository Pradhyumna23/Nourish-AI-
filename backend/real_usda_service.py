"""
Real USDA FoodData Central API integration.
Replace the mock food search with actual USDA database calls.
"""

import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional

class USDAService:
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        
    async def search_foods(self, query: str, page_size: int = 20) -> Dict[str, Any]:
        """Search for foods in USDA FoodData Central database."""
        
        search_url = f"{self.base_url}/foods/search"
        
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy", "Branded"],
            "sortBy": "dataType.keyword",
            "sortOrder": "asc"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Transform USDA response to our format
                foods = []
                for food in data.get("foods", []):
                    food_item = {
                        "fdc_id": food.get("fdcId"),
                        "description": food.get("description", ""),
                        "brand_owner": food.get("brandOwner", ""),
                        "food_category": food.get("foodCategory", ""),
                        "data_type": food.get("dataType", ""),
                        "nutrients": self._extract_nutrients(food.get("foodNutrients", []))
                    }
                    foods.append(food_item)
                
                return {
                    "foods": foods,
                    "total_hits": data.get("totalHits", 0),
                    "current_page": data.get("currentPage", 1),
                    "total_pages": data.get("totalPages", 1)
                }
                
        except Exception as e:
            print(f"USDA API Error: {e}")
            return {"foods": [], "total_hits": 0, "current_page": 1, "total_pages": 1}
    
    async def get_food_details(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed nutrition information for a specific food."""
        
        detail_url = f"{self.base_url}/food/{fdc_id}"
        
        params = {
            "api_key": self.api_key,
            "nutrients": "203,204,205,208,269,291,301,303,304,305,306,307,401,404,405,406,410,415,418,421,430"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(detail_url, params=params)
                response.raise_for_status()
                
                food = response.json()
                
                return {
                    "fdc_id": food.get("fdcId"),
                    "description": food.get("description", ""),
                    "brand_owner": food.get("brandOwner", ""),
                    "food_category": food.get("foodCategory", ""),
                    "nutrients": self._extract_nutrients(food.get("foodNutrients", [])),
                    "serving_sizes": self._extract_serving_sizes(food.get("foodPortions", []))
                }
                
        except Exception as e:
            print(f"USDA Food Detail Error: {e}")
            return None
    
    def _extract_nutrients(self, food_nutrients: List[Dict]) -> Dict[str, float]:
        """Extract and normalize nutrient data."""
        
        # USDA nutrient ID mapping
        nutrient_map = {
            208: "calories",           # Energy
            203: "protein_g",          # Protein
            204: "fat_g",              # Total lipid (fat)
            205: "carbs_g",            # Carbohydrate, by difference
            269: "sugar_g",            # Sugars, total
            291: "fiber_g",            # Fiber, total dietary
            301: "calcium_mg",         # Calcium, Ca
            303: "iron_mg",            # Iron, Fe
            304: "magnesium_mg",       # Magnesium, Mg
            305: "phosphorus_mg",      # Phosphorus, P
            306: "potassium_mg",       # Potassium, K
            307: "sodium_mg",          # Sodium, Na
            401: "vitamin_c_mg",       # Vitamin C, total ascorbic acid
            404: "thiamin_mg",         # Thiamin
            405: "riboflavin_mg",      # Riboflavin
            406: "niacin_mg",          # Niacin
            410: "pantothenic_acid_mg", # Pantothenic acid
            415: "vitamin_b6_mg",      # Vitamin B-6
            418: "vitamin_b12_mcg",    # Vitamin B-12
            421: "choline_mg",         # Choline, total
            430: "vitamin_k_mcg"       # Vitamin K (phylloquinone)
        }
        
        nutrients = {}
        
        for nutrient in food_nutrients:
            nutrient_id = nutrient.get("nutrient", {}).get("id")
            amount = nutrient.get("amount", 0)
            
            if nutrient_id in nutrient_map:
                nutrients[nutrient_map[nutrient_id]] = round(amount, 2)
        
        return nutrients
    
    def _extract_serving_sizes(self, food_portions: List[Dict]) -> List[Dict[str, Any]]:
        """Extract serving size information."""
        
        serving_sizes = []
        
        # Add default 100g serving
        serving_sizes.append({
            "unit": "gram",
            "value": 100.0,
            "description": "100 grams"
        })
        
        for portion in food_portions:
            if portion.get("gramWeight") and portion.get("modifier"):
                serving_sizes.append({
                    "unit": "serving",
                    "value": 1.0,
                    "description": portion.get("modifier", "1 serving"),
                    "gram_weight": portion.get("gramWeight")
                })
        
        return serving_sizes

# Example usage function
async def test_usda_integration():
    """Test the USDA API integration."""
    
    usda = USDAService()
    
    # Test search
    print("🔍 Testing USDA Food Search...")
    search_results = await usda.search_foods("apple", 5)
    print(f"Found {search_results['total_hits']} foods")
    
    if search_results['foods']:
        first_food = search_results['foods'][0]
        print(f"First result: {first_food['description']}")
        
        # Test food details
        print(f"\n📊 Getting details for FDC ID: {first_food['fdc_id']}")
        details = await usda.get_food_details(first_food['fdc_id'])
        
        if details:
            print(f"Calories per 100g: {details['nutrients'].get('calories', 'N/A')}")
            print(f"Protein: {details['nutrients'].get('protein_g', 'N/A')}g")
            print(f"Carbs: {details['nutrients'].get('carbs_g', 'N/A')}g")
            print(f"Fat: {details['nutrients'].get('fat_g', 'N/A')}g")

if __name__ == "__main__":
    asyncio.run(test_usda_integration())
