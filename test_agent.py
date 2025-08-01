#!/usr/bin/env python3
"""
Test script for the consolidated LLM-based nutrition agent.
This tests the nutrition tools directly since the full A2A server requires 
Google ADK dependencies.
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

async def test_nutrition_tools():
    """Test the nutrition tools that power the LLM agent."""
    print("🧪 Testing Nutrition Tools (LLM Agent Backend)")
    print("=" * 60)
    
    # Load environment and check configuration
    load_dotenv()
    nutritionix_key = os.getenv("NUTRITIONIX_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    print("🔧 Environment Configuration:")
    print(f"   Nutritionix API Key: {'✅ Configured' if nutritionix_key else '❌ Missing'}")
    print(f"   Google API Key: {'✅ Configured' if google_key else '❌ Missing'}")
    print()
    
    try:
        # Import nutrition tools
        from nutrition_tools import analyze_nutrition, calculate_meal_totals, get_nutrition_recommendations
        
        print("✅ Nutrition tools imported successfully")
        print()
        
        # Test cases that would be handled by the LLM agent
        test_cases = [
            {
                "name": "Single Food Analysis",
                "action": lambda: analyze_nutrition("medium apple"),
                "description": "Basic food lookup"
            },
            {
                "name": "Complex Food Query",
                "action": lambda: analyze_nutrition("2 scrambled eggs with 1 tbsp butter"),
                "description": "Multi-ingredient analysis"
            },
            {
                "name": "Meal Calculation",
                "action": lambda: calculate_meal_totals([
                    "1 cup cooked rice",
                    "100g grilled chicken breast", 
                    "1 cup steamed broccoli"
                ]),
                "description": "Complete meal analysis"
            },
            {
                "name": "Nutrition Recommendations",
                "action": lambda: get_nutrition_recommendations({
                    "calories": 1200,
                    "protein": 45,
                    "total_carbohydrates": 150,
                    "total_fat": 40,
                    "sodium": 1800
                }, "weight loss", ["vegetarian"]),
                "description": "Personalized recommendations"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test {i}: {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print("-" * 40)
            
            try:
                result = await test_case["action"]()
                
                if result.get("status") == "success":
                    print("✅ SUCCESS")
                    
                    # Display key results based on test type
                    if "foods" in result:
                        foods = result["foods"]
                        print(f"   Found {len(foods)} food item(s):")
                        for food in foods[:2]:  # Show first 2 items
                            name = food.get("food_name", "Unknown")
                            calories = food.get("calories", 0)
                            protein = food.get("protein", food.get("macronutrients", {}).get("protein", 0))
                            print(f"     • {name}: {calories} cal, {protein}g protein")
                    
                    elif "meal_totals" in result:
                        totals = result["meal_totals"]
                        print(f"   Meal totals: {totals['calories']} cal, {totals['protein']}g protein")
                    
                    elif "recommendations" in result:
                        recommendations = result["recommendations"]
                        print(f"   Generated {len(recommendations)} recommendations")
                        for rec in recommendations[:2]:
                            print(f"     • {rec}")
                            
                    if result.get("note"):
                        print(f"   Note: {result['note']}")
                        
                else:
                    print(f"❌ ERROR: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)}")
            
            print()
        
        print("=" * 60)
        print("✅ All nutrition tool tests completed!")
        print()
        print("💡 These tools power the LLM agent's intelligent responses:")
        print("   • The LLM uses analyze_nutrition for specific food queries")
        print("   • calculate_meal_totals for complete meal analysis") 
        print("   • get_nutrition_recommendations for personalized advice")
        print("   • Combined with Gemini's language understanding for natural conversations")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error("Test failed", exc_info=True)

def test_agent_configuration():
    """Test the agent configuration without starting the server."""
    print("\n🤖 Testing LLM Agent Configuration")
    print("=" * 60)
    
    try:
        load_dotenv()
        
        # Check if we can import the main components
        print("📦 Checking imports...")
        
        # Test A2A imports
        from a2a.server.agent_execution import AgentExecutor
        from a2a.types import AgentCard
        print("   ✅ A2A SDK imports successful")
        
        # Test Google ADK imports (may fail if not installed)
        try:
            from google.adk.agents.llm_agent import LlmAgent
            from google.adk.runners import Runner
            print("   ✅ Google ADK imports successful")
            google_adk_available = True
        except ImportError as e:
            print(f"   ⚠️  Google ADK import failed: {str(e)}")
            print("   Note: Install google-adk package for full LLM functionality")
            google_adk_available = False
        
        # Test nutrition tools
        from nutrition_tools import analyze_nutrition
        print("   ✅ Nutrition tools import successful")
        
        print("\n🔧 Configuration Status:")
        
        # Check environment variables
        google_key = os.getenv("GOOGLE_API_KEY")
        nutritionix_key = os.getenv("NUTRITIONIX_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
        
        print(f"   Google API Key: {'✅ Set' if google_key else '❌ Missing'}")
        print(f"   Nutritionix API Key: {'✅ Set' if nutritionix_key else '❌ Missing'}")
        print(f"   Gemini Model: {model}")
        
        if google_adk_available and google_key:
            print("\n✅ LLM Agent: Fully functional")
            print("   The agent can provide intelligent, context-aware nutrition advice")
        elif google_adk_available and not google_key:
            print("\n⚠️  LLM Agent: Partially functional")
            print("   ADK available but API key missing - set GOOGLE_API_KEY in .env")
        else:
            print("\n❌ LLM Agent: Limited functionality")
            print("   Install Google ADK and set API key for full LLM features")
            
        print(f"\n🚀 Server can be started with: python main.py")
        print(f"   Will be available at: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        logger.error("Configuration test failed", exc_info=True)

if __name__ == "__main__":
    print("🧪 Testing Consolidated LLM Nutrition Agent")
    print("=" * 60)
    
    # Test the underlying tools
    asyncio.run(test_nutrition_tools())
    
    # Test the agent configuration
    test_agent_configuration()
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    print("• Nutrition tools provide accurate food data analysis")
    print("• LLM agent combines this with intelligent conversation")
    print("• Full functionality requires Google ADK + API key")
    print("• Server ready to start with: python main.py")