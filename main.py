import os
import json
import uvicorn
import httpx
import logging
from datetime import datetime
from dotenv import load_dotenv

from typing import Dict, Any, Optional

from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.types import (
    AgentCard,
    AgentProvider,
    AgentSkill,
    AgentCapabilities,
)
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError, UnsupportedOperationError
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler, RequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NutritionAgentExecutor(AgentExecutor):
    """A2A Agent Executor for nutrition queries using Nutritionix API."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing NutritionAgentExecutor")
        
        load_dotenv()
        self.nutritionix_api_key = os.getenv("NUTRITIONIX_API_KEY")
        self.nutritionix_app_id = os.getenv("NUTRITIONIX_APP_ID", "039db79f")
        self.base_url = "https://trackapi.nutritionix.com/v2"
        self.client = httpx.AsyncClient()
        
        logger.info(f"Nutritionix API configuration - App ID: {self.nutritionix_app_id}")
        logger.info(f"API Key present: {bool(self.nutritionix_api_key)}")
        
        if not self.nutritionix_api_key:
            logger.error("NUTRITIONIX_API_KEY environment variable is required")
            raise ValueError("NUTRITIONIX_API_KEY environment variable is required")
        
        logger.info("NutritionAgentExecutor initialized successfully")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute method required by AgentExecutor interface."""
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        logger.info(f"[{request_id}] Starting request execution")
        
        try:
            # Extract task information from context
            message_parts = context.message.parts if context.message else []
            task_data = {}
            task_type = "process_request"
            
            logger.debug(f"[{request_id}] Message parts count: {len(message_parts)}")

            # Parse message content to extract task type and data
            if message_parts and len(message_parts) > 0:
                if hasattr(message_parts[0], "text"):
                    message_text = message_parts[0].text
                    logger.info(f"[{request_id}] Received message: {message_text[:100]}...")
                    
                    try:
                        # Try to parse as JSON for structured requests
                        parsed_data = json.loads(message_text)
                        task_type = parsed_data.get("task_type", "process_request")
                        task_data = parsed_data.get("data", {})
                        logger.info(f"[{request_id}] Parsed as JSON - Task type: {task_type}")
                    except (json.JSONDecodeError, AttributeError):
                        # Handle as plain text request
                        task_data = {"message": message_text}
                        logger.info(f"[{request_id}] Treating as plain text request")

            # Process the task
            logger.info(f"[{request_id}] Processing task type: {task_type}")
            result = await self._handle_task(task_type, task_data)
            logger.info(f"[{request_id}] Task completed successfully")

            await event_queue.enqueue_event(
                new_agent_text_message(json.dumps(result, indent=2))
            )
            logger.info(f"[{request_id}] Response sent to event queue")

        except Exception as e:
            logger.error(f"[{request_id}] Error during execution: {str(e)}", exc_info=True)
            await event_queue.enqueue_event(new_agent_text_message(f"Error: {str(e)}"))

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())

    async def _handle_task(
        self, task_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle different task types for nutrition queries."""
        logger.info(f"Handling task type: {task_type} with data keys: {list(data.keys())}")
        
        if task_type == "process_request":
            return await self._process_request(data)
        elif task_type == "nutrition_query":
            query = data.get("query", "")
            logger.info(f"Direct nutrition query: {query}")
            return await self._get_nutrition_info(query)
        else:
            logger.warning(f"Unknown task type received: {task_type}")
            return {"error": f"Unknown task type: {task_type}"}

    async def _process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process nutrition-related requests."""
        message = data.get("message", "No message provided")
        logger.info(f"Processing request with message: {message}")

        # Detect if this is a nutrition query
        nutrition_keywords = [
            "calories",
            "nutrition",
            "protein",
            "carbs",
            "fat",
            "nutrients",
            "food",
        ]
        
        message_lower = message.lower()
        matched_keywords = [kw for kw in nutrition_keywords if kw in message_lower]
        
        if matched_keywords:
            logger.info(f"Detected nutrition query with keywords: {matched_keywords}")
            return await self._get_nutrition_info(message)

        logger.info("No nutrition keywords detected, returning general response")
        # Default response for non-nutrition queries
        return {
            "status": "success",
            "response": "I'm a nutrition assistant. Ask me about the nutritional content of foods!",
            "agent": "NutritionAgent",
            "suggestions": [
                "Try asking: 'What are the calories in 1 cup of rice?'",
                "Or: 'Show me nutrition info for an apple'",
                "Or: 'How much protein is in chicken breast?'",
            ],
        }

    async def _get_nutrition_info(self, query: str) -> Dict[str, Any]:
        """Get nutrition information for a food query using Nutritionix API."""
        logger.info(f"Getting nutrition info for query: '{query}'")
        
        if not query.strip():
            logger.warning("Empty query provided")
            return {
                "status": "error",
                "message": "Please provide a food item to analyze",
            }

        # First try the real API
        try:
            headers = {
                "x-app-id": self.nutritionix_app_id,
                "x-app-key": self.nutritionix_api_key,
                "Content-Type": "application/json",
            }

            payload = {"query": query, "timezone": "US/Eastern"}
            logger.info(f"Making API request to Nutritionix with payload: {payload}")

            response = await self.client.post(
                f"{self.base_url}/natural/nutrients",
                json=payload,
                headers=headers,
                timeout=5.0,
            )
            
            logger.info(f"API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully received API data with {len(data.get('foods', []))} food items")
                logger.debug(f"API response data: {json.dumps(data, indent=2)[:500]}...")
                return self._format_nutrition_response(data, query)
            elif response.status_code == 401:
                logger.warning("API authentication failed (401), falling back to mock data")
                return self._get_mock_nutrition_data(query)
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text[:200]}")
                return {
                    "status": "error",
                    "message": f"API request failed: {response.status_code}",
                    "query": query,
                }

        except Exception as e:
            logger.error(f"Exception during API request: {str(e)}", exc_info=True)
            logger.info("Falling back to mock data due to exception")
            return self._get_mock_nutrition_data(query)

    def _get_mock_nutrition_data(self, query: str) -> Dict[str, Any]:
        """Return mock nutrition data for demonstration purposes."""
        logger.info(f"Using mock data for query: '{query}'")
        
        mock_data = {
            "apple": {
                "food_name": "Apple, raw",
                "serving_qty": 1,
                "serving_unit": "medium",
                "nf_calories": 95,
                "nf_total_fat": 0.3,
                "nf_saturated_fat": 0.1,
                "nf_cholesterol": 0,
                "nf_sodium": 2,
                "nf_total_carbohydrate": 25,
                "nf_dietary_fiber": 4,
                "nf_sugars": 19,
                "nf_protein": 0.5,
                "nf_potassium": 195,
            },
            "rice": {
                "food_name": "Rice, white, cooked",
                "serving_qty": 1,
                "serving_unit": "cup",
                "nf_calories": 205,
                "nf_total_fat": 0.4,
                "nf_saturated_fat": 0.1,
                "nf_cholesterol": 0,
                "nf_sodium": 2,
                "nf_total_carbohydrate": 45,
                "nf_dietary_fiber": 0.6,
                "nf_sugars": 0.1,
                "nf_protein": 4.3,
                "nf_potassium": 55,
            },
            "chicken": {
                "food_name": "Chicken breast, grilled",
                "serving_qty": 100,
                "serving_unit": "g",
                "nf_calories": 165,
                "nf_total_fat": 3.6,
                "nf_saturated_fat": 1.0,
                "nf_cholesterol": 85,
                "nf_sodium": 74,
                "nf_total_carbohydrate": 0,
                "nf_dietary_fiber": 0,
                "nf_sugars": 0,
                "nf_protein": 31,
                "nf_potassium": 256,
            },
        }

        # Simple keyword matching for mock data
        query_lower = query.lower()
        for keyword, data in mock_data.items():
            if keyword in query_lower:
                logger.info(f"Found mock data match for keyword: '{keyword}'")
                return {
                    "status": "success",
                    "query": query,
                    "foods": [self._format_food_data(data)],
                    "total_foods_found": 1,
                    "note": "Using mock data for demonstration. Please ensure valid Nutritionix API credentials for real data.",
                }

        logger.info(f"No specific mock data found, using generic response for: '{query}'")
        # Default response for unknown foods
        return {
            "status": "success",
            "query": query,
            "foods": [
                {
                    "food_name": f"Generic food item: {query}",
                    "serving_qty": 1,
                    "serving_unit": "serving",
                    "calories": 100,
                    "total_fat": 2.0,
                    "saturated_fat": 0.5,
                    "cholesterol": 0,
                    "sodium": 50,
                    "total_carbohydrate": 20,
                    "dietary_fiber": 2,
                    "sugars": 5,
                    "protein": 3,
                    "potassium": 100,
                }
            ],
            "total_foods_found": 1,
            "note": "Using estimated values for demonstration. Please ensure valid Nutritionix API credentials for accurate data.",
        }

    def _format_food_data(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format food data into consistent structure."""
        logger.debug(f"Formatting food data for: {food_data.get('food_name', 'Unknown')}")
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
            "potassium": round(food_data.get("nf_potassium", 0), 1),
        }

    def _format_nutrition_response(
        self, api_data: Dict[str, Any], original_query: str
    ) -> Dict[str, Any]:
        """Format the Nutritionix API response into a user-friendly format."""
        logger.info(f"Formatting nutrition response for query: '{original_query}'")
        
        foods = api_data.get("foods", [])
        logger.info(f"Processing {len(foods)} food items from API response")

        if not foods:
            logger.warning(f"No foods found in API response for query: '{original_query}'")
            return {
                "status": "error",
                "message": "No nutrition information found for the requested food",
                "query": original_query,
            }

        formatted_foods = []
        for i, food in enumerate(foods):
            food_name = food.get("food_name", "Unknown")
            logger.debug(f"Formatting food {i+1}: {food_name}")
            
            formatted_food = {
                "food_name": food_name,
                "brand_name": food.get("brand_name"),
                "serving_qty": food.get("serving_qty", 1),
                "serving_unit": food.get("serving_unit", "serving"),
                "calories": round(food.get("nf_calories", 0), 1),
                "total_fat": round(food.get("nf_total_fat", 0), 1),
                "saturated_fat": round(food.get("nf_saturated_fat", 0), 1),
                "cholesterol": round(food.get("nf_cholesterol", 0), 1),
                "sodium": round(food.get("nf_sodium", 0), 1),
                "total_carbohydrate": round(food.get("nf_total_carbohydrate", 0), 1),
                "dietary_fiber": round(food.get("nf_dietary_fiber", 0), 1),
                "sugars": round(food.get("nf_sugars", 0), 1),
                "protein": round(food.get("nf_protein", 0), 1),
                "potassium": round(food.get("nf_potassium", 0), 1),
            }
            formatted_foods.append(formatted_food)

        logger.info(f"Successfully formatted {len(formatted_foods)} food items")
        return {
            "status": "success",
            "query": original_query,
            "foods": formatted_foods,
            "total_foods_found": len(formatted_foods),
        }


# Create agent card
agent_card = AgentCard(
    name="NutritionAgent",
    description="A2A agent that provides nutritional information for foods using the Nutritionix API",
    version="1.0.0",
    url=os.getenv("HU_APP_URL") or "http://localhost:8000",
    capabilities=AgentCapabilities(
        streaming=True, push_notifications=False, state_transition_history=True
    ),
    skills=[
        AgentSkill(
            id="nutrition_query",
            name="Nutrition Query",
            description="Get detailed nutritional information for foods and beverages",
            tags=["nutrition", "health", "food", "calories", "macros"],
            examples=[
                "What are the calories in 1 cup of rice?",
                "Show me nutrition info for an apple",
                "How much protein is in chicken breast?",
                "Nutrition facts for 2 slices of pizza",
            ],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        ),
        AgentSkill(
            id="process_request",
            name="General Request Processing",
            description="Handle general requests and provide nutrition guidance",
            tags=["nutrition", "assistant", "food"],
            examples=["Help with nutrition questions", "Food analysis"],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        ),
    ],
    default_input_modes=["application/json", "text/plain"],
    default_output_modes=["application/json", "text/plain"],
    provider=AgentProvider(
        organization="Nutrition Assistant",
        url="https://www.nutritionix.com",
    ),
)

# Create the A2A Starlette application
agent_executor = NutritionAgentExecutor()

request_handler = DefaultRequestHandler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
)
app = A2AStarletteApplication(
    agent_card=agent_card, http_handler=request_handler
).build()

if __name__ == "__main__":
    logger.info("Starting Nutrition A2A Agent server")
    logger.info("Server will be available at http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
