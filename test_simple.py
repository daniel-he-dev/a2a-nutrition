#!/usr/bin/env python3
"""
Simplified test of the nutrition functionality without A2A SDK
"""
import asyncio
import httpx
import json
from dotenv import load_dotenv
import os
from typing import Dict, Any

class SimpleNutritionAgent:
    """Simplified nutrition agent for testing"""
    
    def __init__(self):
        load_dotenv()
        self.nutritionix_api_key = os.getenv("NUTRITIONIX_API_KEY")
        self.nutritionix_app_id = os.getenv("NUTRITIONIX_APP_ID", "039db79f")
        self.base_url = "https://trackapi.nutritionix.com/v2"
        self.client = httpx.AsyncClient()
        
    async def get_nutrition_info(self, query: str) -> Dict[str, Any]:
        """Get nutrition information for a food query"""
        if not query.strip():
            return {"status": "error", "message": "Please provide a food item to analyze"}
        
        # Try the real API first
        try:
            headers = {
                "x-app-id": self.nutritionix_app_id,
                "x-app-key": self.nutritionix_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {"query": query, "timezone": "US/Eastern"}
            
            response = await self.client.post(
                f"{self.base_url}/natural/nutrients",
                json=payload,
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._format_nutrition_response(data, query)
            elif response.status_code == 401:
                return self._get_mock_nutrition_data(query)
            else:
                return {"status": "error", "message": f"API request failed: {response.status_code}"}
                
        except Exception:
            return self._get_mock_nutrition_data(query)
    
    def _get_mock_nutrition_data(self, query: str) -> Dict[str, Any]:
        """Return mock nutrition data for demonstration"""
        mock_data = {
            "apple": {
                "food_name": "Apple, raw", "serving_qty": 1, "serving_unit": "medium",
                "nf_calories": 95, "nf_total_fat": 0.3, "nf_saturated_fat": 0.1,
                "nf_cholesterol": 0, "nf_sodium": 2, "nf_total_carbohydrate": 25,
                "nf_dietary_fiber": 4, "nf_sugars": 19, "nf_protein": 0.5, "nf_potassium": 195
            },
            "rice": {
                "food_name": "Rice, white, cooked", "serving_qty": 1, "serving_unit": "cup",
                "nf_calories": 205, "nf_total_fat": 0.4, "nf_saturated_fat": 0.1,
                "nf_cholesterol": 0, "nf_sodium": 2, "nf_total_carbohydrate": 45,
                "nf_dietary_fiber": 0.6, "nf_sugars": 0.1, "nf_protein": 4.3, "nf_potassium": 55
            },
            "chicken": {
                "food_name": "Chicken breast, grilled", "serving_qty": 100, "serving_unit": "g",
                "nf_calories": 165, "nf_total_fat": 3.6, "nf_saturated_fat": 1.0,
                "nf_cholesterol": 85, "nf_sodium": 74, "nf_total_carbohydrate": 0,
                "nf_dietary_fiber": 0, "nf_sugars": 0, "nf_protein": 31, "nf_potassium": 256
            }
        }
        
        query_lower = query.lower()
        for keyword, data in mock_data.items():
            if keyword in query_lower:
                return {
                    "status": "success", "query": query,
                    "foods": [self._format_food_data(data)], "total_foods_found": 1,
                    "note": "Using mock data for demonstration. Please ensure valid Nutritionix API credentials for real data."
                }
        
        return {
            "status": "success", "query": query,
            "foods": [{
                "food_name": f"Generic food item: {query}", "serving_qty": 1, "serving_unit": "serving",
                "calories": 100, "total_fat": 2.0, "saturated_fat": 0.5, "cholesterol": 0,
                "sodium": 50, "total_carbohydrate": 20, "dietary_fiber": 2, "sugars": 5,
                "protein": 3, "potassium": 100
            }],
            "total_foods_found": 1,
            "note": "Using estimated values for demonstration."
        }
    
    def _format_food_data(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format food data into consistent structure"""
        return {
            "food_name": food_data.get("food_name", "Unknown"),
            "serving_qty": food_data.get("serving_qty", 1),
            "serving_unit": food_data.get("serving_unit", "serving"),
            "calories": round(food_data.get("nf_calories", 0), 1),
            "total_fat": round(food_data.get("nf_total_fat", 0), 1),
            "saturated_fat": round(food_data.get("nf_saturated_fat", 0), 1),
            "cholesterol": round(food_data.get("nf_cholesterol", 0), 1),
            "sodium": round(food_data.get("nf_sodium", 0), 1),
            "total_carbohydrate": round(food_data.get("nf_total_carbohydrate", 0), 1),
            "dietary_fiber": round(food_data.get("nf_dietary_fiber", 0), 1),
            "sugars": round(food_data.get("nf_sugars", 0), 1),
            "protein": round(food_data.get("nf_protein", 0), 1),
            "potassium": round(food_data.get("nf_potassium", 0), 1)
        }
    
    def _format_nutrition_response(self, api_data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Format the Nutritionix API response"""
        foods = api_data.get("foods", [])
        if not foods:
            return {"status": "error", "message": "No nutrition information found", "query": original_query}
        
        formatted_foods = [self._format_food_data(food) for food in foods]
        return {
            "status": "success", "query": original_query,
            "foods": formatted_foods, "total_foods_found": len(formatted_foods)
        }

async def test_nutrition_agent():
    """Test the nutrition agent"""
    print("🧪 Testing Simple Nutrition Agent")
    print("=" * 50)
    
    agent = SimpleNutritionAgent()
    
    test_queries = [
        "apple",
        "1 cup rice", 
        "chicken breast 100g",
        "banana",
        "unknown food item"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        result = await agent.get_nutrition_info(query)
        
        if result["status"] == "success":
            for food in result["foods"]:
                print(f"✅ {food['food_name']}")
                print(f"   Serving: {food['serving_qty']} {food['serving_unit']}")
                print(f"   Calories: {food['calories']}")
                print(f"   Protein: {food['protein']}g")
                print(f"   Carbs: {food['total_carbohydrate']}g")
                print(f"   Fat: {food['total_fat']}g")
                if result.get("note"):
                    print(f"   Note: {result['note']}")
        else:
            print(f"❌ Error: {result['message']}")
    
    await agent.client.aclose()
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_nutrition_agent())