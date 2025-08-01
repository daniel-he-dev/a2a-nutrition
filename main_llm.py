"""
LLM-based A2A Nutrition Agent Server
Enhanced with Google ADK for intelligent nutrition analysis and recommendations.
"""

import os
import json
import uvicorn
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from a2a.server.tasks import InMemoryTaskStore, new_task, TaskUpdater, TaskState
from a2a.server.apps import A2AStarletteApplication
from a2a.types import (
    AgentCard,
    AgentProvider,
    AgentSkill,
    AgentCapabilities,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError, UnsupportedOperationError
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler, RequestHandler

# Import our LLM nutrition agent
from llm_nutrition_agent import LLMNutritionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMNutritionAgentExecutor(AgentExecutor):
    """A2A Agent Executor for LLM-based nutrition analysis and recommendations."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing LLM Nutrition Agent Executor")
        
        load_dotenv()
        
        # Verify required environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key or google_api_key == "your_google_api_key_here":
            logger.warning("GOOGLE_API_KEY not set or using placeholder. LLM features may not work.")
        
        # Initialize the LLM nutrition agent
        try:
            self.nutrition_agent = LLMNutritionAgent()
            logger.info("LLM Nutrition Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM agent: {str(e)}")
            raise

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute method required by AgentExecutor interface with LLM streaming."""
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        logger.info(f"[{request_id}] Starting LLM request execution")
        
        try:
            # Extract the user's message
            message_parts = context.message.parts if context.message else []
            user_message = ""
            
            if message_parts and len(message_parts) > 0:
                if hasattr(message_parts[0], "text"):
                    user_message = message_parts[0].text
                    logger.info(f"[{request_id}] User message: {user_message[:200]}...")
            
            if not user_message.strip():
                await event_queue.enqueue_event(
                    new_agent_text_message("Please provide a nutrition-related question or food description to analyze.")
                )
                return
            
            # Check if this is a continuing task or new task
            task = context.current_task
            session_id = None
            
            if not task:
                # Create new task for this conversation
                logger.info(f"[{request_id}] Creating new task")
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
                session_id = task.id  # Use task ID as session ID
            else:
                session_id = task.contextId or task.id
                logger.info(f"[{request_id}] Continuing task with session: {session_id}")
            
            # Create task updater for streaming updates
            updater = TaskUpdater(event_queue, task.id, session_id)
            
            # Stream responses from the LLM agent
            logger.info(f"[{request_id}] Starting LLM streaming for session: {session_id}")
            
            has_updates = False
            async for response_chunk in self.nutrition_agent.stream(user_message, session_id):
                if response_chunk.get("is_task_complete", False):
                    # Final response - complete the task
                    final_content = response_chunk.get("content", "")
                    logger.info(f"[{request_id}] Task completed with final response")
                    
                    # Add the response as an artifact and complete the task
                    await updater.add_artifact(
                        [Part(root=TextPart(text=final_content))],
                        name="nutrition_analysis"
                    )
                    await updater.complete()
                    break
                else:
                    # Intermediate update
                    update_content = response_chunk.get("updates", "")
                    if update_content:
                        has_updates = True
                        logger.debug(f"[{request_id}] Streaming update: {update_content[:100]}...")
                        
                        await updater.update_status(
                            TaskState.working,
                            new_agent_text_message(update_content, session_id, task.id)
                        )
            
            if not has_updates:
                logger.warning(f"[{request_id}] No updates received from LLM agent")
                await updater.add_artifact(
                    [Part(root=TextPart(text="I'm sorry, I couldn't process your request. Please try again."))],
                    name="error_response"
                )
                await updater.complete()

        except Exception as e:
            logger.error(f"[{request_id}] Error during LLM execution: {str(e)}", exc_info=True)
            error_message = f"An error occurred while processing your nutrition query: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_message))

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current request."""
        logger.info("Cancelling nutrition agent request")
        raise ServerError(error=UnsupportedOperationError())

# Create enhanced agent card for LLM-powered nutrition agent
agent_card = AgentCard(
    name="AI Nutrition Assistant",
    description="Intelligent nutrition analysis and meal planning assistant powered by advanced AI. Get personalized nutrition insights, meal analysis, and dietary recommendations.",
    version="2.0.0",
    url=os.getenv("HU_APP_URL") or "http://localhost:8000",
    capabilities=AgentCapabilities(
        streaming=True, 
        push_notifications=False, 
        state_transition_history=True
    ),
    skills=[
        AgentSkill(
            id="intelligent_nutrition_analysis",
            name="Intelligent Nutrition Analysis",
            description="AI-powered analysis of foods and meals with personalized insights and recommendations",
            tags=["nutrition", "AI", "health", "analysis", "personalized", "smart"],
            examples=[
                "Analyze the nutrition in my breakfast: scrambled eggs, toast, and orange juice",
                "What are the health benefits of eating salmon twice a week?",
                "I'm trying to lose weight - is this meal good for me?",
                "Calculate the total nutrition for my lunch: chicken salad sandwich and apple",
                "What foods should I eat to get more protein in my diet?",
                "Compare the nutrition between brown rice and quinoa",
                "I'm diabetic - help me plan a low-carb dinner",
                "What are the nutritional differences between grass-fed and regular beef?"
            ],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        ),
        AgentSkill(
            id="meal_planning_assistant",
            name="AI Meal Planning",
            description="Intelligent meal planning with dietary restrictions, preferences, and health goals",
            tags=["meal-planning", "dietary-restrictions", "health-goals", "AI"],
            examples=[
                "Help me plan a high-protein meal for post-workout",
                "Suggest a heart-healthy dinner with less than 500 calories",
                "I'm vegetarian and need more iron - what should I eat?",
                "Plan a diabetic-friendly breakfast with good fiber content"
            ],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        ),
        AgentSkill(
            id="nutrition_education",
            name="Nutrition Education & Guidance",
            description="Educational content about nutrition science, health recommendations, and dietary guidance",
            tags=["education", "health", "science", "guidance"],
            examples=[
                "Explain the role of antioxidants in my diet",
                "What's the difference between good and bad cholesterol?",
                "How much water should I drink per day?",
                "What are the signs of vitamin D deficiency?"
            ],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        )
    ],
    default_input_modes=["application/json", "text/plain"],
    default_output_modes=["application/json", "text/plain"],
    provider=AgentProvider(
        organization="AI Nutrition Solutions",
        url="https://www.nutritionix.com",
    ),
)

# Create the A2A Starlette application with LLM agent
agent_executor = LLMNutritionAgentExecutor()

request_handler = DefaultRequestHandler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card, 
    http_handler=request_handler
).build()

if __name__ == "__main__":
    logger.info("Starting LLM-powered AI Nutrition Assistant")
    logger.info("Enhanced with Google ADK for intelligent responses")
    logger.info("Server will be available at http://0.0.0.0:8000")
    
    # Check environment setup
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key or google_api_key == "your_google_api_key_here":
        logger.warning("⚠️  GOOGLE_API_KEY not properly configured. Please set your Google API key in .env file.")
        logger.warning("⚠️  The agent will use fallback nutrition data until the API key is configured.")
    else:
        logger.info("✅ Google API key configured - LLM features enabled")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)