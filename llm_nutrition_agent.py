"""
LLM-based Nutrition Agent using Google ADK.
This agent provides intelligent nutrition analysis and personalized recommendations.
"""

import os
import logging
from typing import Dict, Any, Optional, AsyncIterable
from dotenv import load_dotenv

# Google ADK and Gemini imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.services.artifact_service import InMemoryArtifactService
from google.adk.services.session_service import InMemorySessionService
from google.adk.services.memory_service import InMemoryMemoryService

# Import our nutrition tools
from nutrition_tools import analyze_nutrition, calculate_meal_totals, get_nutrition_recommendations

logger = logging.getLogger(__name__)

class LLMNutritionAgent:
    """LLM-powered nutrition analysis agent using Google ADK."""
    
    def __init__(self, user_id: str = "default_user"):
        load_dotenv()
        
        self._user_id = user_id
        self._model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
        
        logger.info(f"Initializing LLM nutrition agent with model: {self._model}")
        
        # Build the LLM agent with nutrition-specific instructions
        self._agent = self._build_agent()
        
        # Create runner with services for session management
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        logger.info("LLM nutrition agent initialized successfully")
    
    def _build_agent(self) -> LlmAgent:
        """Build the LLM agent with nutrition-specific configuration."""
        
        instruction = """
You are a specialized AI nutrition assistant with access to comprehensive food and nutrition data. Your role is to help users understand their nutritional intake, make informed food choices, and achieve their health goals.

CORE CAPABILITIES:
1. Analyze nutritional content of individual foods and complete meals
2. Calculate daily nutrition totals and compare against recommended values  
3. Provide personalized nutrition recommendations
4. Answer questions about nutrition, health, and dietary choices
5. Help with meal planning and food substitutions

INTERACTION PRINCIPLES:
- Always be helpful, accurate, and supportive
- Use the nutrition analysis tools to provide precise data when discussing specific foods
- Consider the user's dietary restrictions, goals, and preferences
- Provide context and explanations, not just raw numbers
- Suggest practical, actionable advice

DECISION PROCESS:
1. If the user asks about specific foods or meals, use the analyze_nutrition or calculate_meal_totals tools
2. If they want recommendations, use get_nutrition_recommendations after analyzing their current intake
3. For general nutrition questions, provide evidence-based information
4. Always explain the nutritional significance of the data you provide

RESPONSE STYLE:
- Be conversational and engaging
- Break down complex nutritional information into understandable terms
- Use specific numbers from your analysis tools when relevant
- Provide actionable next steps or suggestions
- Ask clarifying questions if needed to give better advice

IMPORTANT: Always use the available tools when analyzing specific foods or calculating nutritional values. Don't estimate or guess nutritional information when you have tools available to provide accurate data.
"""
        
        return LlmAgent(
            model=self._model,
            name="nutrition_analysis_agent",
            description="AI-powered nutrition analysis and meal planning assistant with access to comprehensive food database",
            instruction=instruction,
            tools=[
                analyze_nutrition,
                calculate_meal_totals, 
                get_nutrition_recommendations,
            ],
        )
    
    async def stream(self, query: str, session_id: Optional[str] = None) -> AsyncIterable[Dict[str, Any]]:
        """
        Stream responses from the LLM agent.
        
        Args:
            query: User's nutrition-related query
            session_id: Optional session ID for conversation context
            
        Yields:
            Dictionary with response data and completion status
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Get or create session
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )
            
            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    state={},
                    session_id=session_id,
                )
                logger.info(f"Created new session: {session.id}")
            else:
                logger.info(f"Using existing session: {session.id}")
            
            # Stream the LLM response
            response_parts = []
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session.id,
                new_message=query
            ):
                if event.is_final_response():
                    # Final response with complete content
                    if event.content and event.content.parts:
                        full_response = ""
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                full_response += part.text
                        
                        logger.info(f"Completed response generation for session {session.id}")
                        yield {
                            "is_task_complete": True,
                            "content": full_response,
                            "session_id": session.id
                        }
                    else:
                        yield {
                            "is_task_complete": True,
                            "content": "I apologize, but I couldn't generate a proper response. Please try rephrasing your question.",
                            "session_id": session.id
                        }
                else:
                    # Intermediate streaming update
                    if hasattr(event, 'content') and event.content:
                        partial_content = ""
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text'):
                                    partial_content += part.text
                        
                        if partial_content:
                            yield {
                                "is_task_complete": False,
                                "updates": partial_content,
                                "session_id": session.id
                            }
                    else:
                        # Generic processing update
                        yield {
                            "is_task_complete": False,
                            "updates": "Analyzing nutrition data...",
                            "session_id": session.id
                        }
        
        except Exception as e:
            logger.error(f"Error during LLM streaming: {str(e)}", exc_info=True)
            yield {
                "is_task_complete": True,
                "content": f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question.",
                "session_id": session_id
            }
    
    async def get_simple_response(self, query: str, session_id: Optional[str] = None) -> str:
        """
        Get a simple string response (non-streaming).
        
        Args:
            query: User's nutrition-related query
            session_id: Optional session ID for conversation context
            
        Returns:
            Complete response as a string
        """
        logger.info(f"Getting simple response for: {query[:100]}...")
        
        full_response = ""
        async for response_chunk in self.stream(query, session_id):
            if response_chunk["is_task_complete"]:
                full_response = response_chunk["content"]
                break
        
        return full_response
    
    async def analyze_food_query(self, food_description: str) -> Dict[str, Any]:
        """
        Directly analyze a food query and return structured data.
        
        Args:
            food_description: Natural language food description
            
        Returns:
            Structured nutrition analysis data
        """
        logger.info(f"Direct food analysis for: {food_description}")
        return await analyze_nutrition(food_description)
    
    async def close(self):
        """Clean up resources."""
        logger.info("Closing LLM nutrition agent resources")
        # Close any async resources if needed
        pass