#!/usr/bin/env python3
"""
Test script for the LLM-based nutrition agent.
This tests the agent's capabilities without requiring the full A2A server.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_llm_nutrition_agent():
    """Test the LLM nutrition agent with various queries."""
    print("🤖 Testing LLM-powered AI Nutrition Assistant")
    print("=" * 60)
    
    # Load environment and check configuration
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key or google_api_key == "your_google_api_key_here":
        print("⚠️  WARNING: GOOGLE_API_KEY not configured properly")
        print("⚠️  The agent will use mock nutrition data and may not have full LLM capabilities")
        print("⚠️  Please set your Google API key in .env file for full functionality")
        print()
    else:
        print("✅ Google API key configured - LLM features enabled")
        print()
    
    try:
        # Import and initialize the agent
        from llm_nutrition_agent import LLMNutritionAgent
        
        agent = LLMNutritionAgent(user_id="test_user")
        print("✅ LLM Nutrition Agent initialized successfully")
        print()
        
        # Test queries ranging from simple to complex
        test_queries = [
            {
                "query": "What are the calories in a large apple?",
                "description": "Simple food analysis"
            },
            {
                "query": "Analyze my breakfast: 2 scrambled eggs, 2 slices of whole wheat toast with butter, and a glass of orange juice",
                "description": "Complex meal analysis"
            },
            {
                "query": "I'm trying to lose weight and need a high-protein, low-carb lunch suggestion under 400 calories",
                "description": "Personalized meal planning with constraints"
            },
            {
                "query": "Compare the nutritional benefits of salmon vs chicken breast for muscle building",
                "description": "Comparative analysis with context"
            },
            {
                "query": "I'm diabetic and want to know if quinoa is a good rice substitute",
                "description": "Health condition specific advice"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"🔍 Test {i}: {test_case['description']}")
            print(f"Query: \"{test_case['query']}\"")
            print("-" * 60)
            
            try:
                # Test streaming response
                print("📝 Streaming Response:")
                full_response = ""
                
                async for response_chunk in agent.stream(test_case["query"]):
                    if response_chunk.get("is_task_complete", False):
                        # Final response
                        final_content = response_chunk.get("content", "")
                        if final_content != full_response:  # Only print if different from streamed content
                            print(final_content)
                        break
                    else:
                        # Streaming update
                        update = response_chunk.get("updates", "")
                        if update and update not in full_response:
                            print(update, end="", flush=True)
                            full_response += update
                
                print("\n" + "="*60 + "\n")
                
            except Exception as e:
                print(f"❌ Error in test {i}: {str(e)}")
                print("="*60 + "\n")
                continue
        
        # Test direct nutrition analysis (tool usage)
        print("🔬 Testing Direct Nutrition Analysis Tool:")
        print("Query: \"1 cup cooked quinoa\"")
        print("-" * 60)
        
        try:
            result = await agent.analyze_food_query("1 cup cooked quinoa")
            print("📊 Nutrition Analysis Result:")
            if result["status"] == "success":
                for food in result["foods"]:
                    print(f"Food: {food['food_name']}")
                    print(f"Serving: {food['serving_qty']} {food['serving_unit']}")
                    print(f"Calories: {food['calories']}")
                    print(f"Protein: {food.get('macronutrients', {}).get('protein', 0)}g")
                    print(f"Carbs: {food.get('macronutrients', {}).get('total_carbohydrates', 0)}g")
                    print(f"Fat: {food.get('macronutrients', {}).get('total_fat', 0)}g")
            else:
                print(f"Error: {result['message']}")
        except Exception as e:
            print(f"❌ Error in direct analysis: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        
        # Clean up
        await agent.close()
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Failed to initialize or test agent: {str(e)}")
        logger.error("Test failed", exc_info=True)

async def test_basic_tools():
    """Test the nutrition tools directly."""
    print("\n🔧 Testing Nutrition Tools Directly")
    print("=" * 60)
    
    try:
        from nutrition_tools import analyze_nutrition, calculate_meal_totals
        
        # Test single food analysis
        print("🍎 Testing single food analysis:")
        result = await analyze_nutrition("medium apple")
        print(f"Result: {result}")
        print()
        
        # Test meal calculation
        print("🍽️ Testing meal calculation:")
        meal_result = await calculate_meal_totals([
            "2 scrambled eggs",
            "1 slice whole wheat toast", 
            "1 tbsp butter"
        ])
        print(f"Meal totals: {meal_result}")
        print()
        
    except Exception as e:
        print(f"❌ Error testing tools: {str(e)}")
        logger.error("Tool test failed", exc_info=True)

if __name__ == "__main__":
    print("Starting LLM Nutrition Agent Tests...")
    print()
    
    # Run the main agent test
    asyncio.run(test_llm_nutrition_agent())
    
    # Run basic tools test
    asyncio.run(test_basic_tools())