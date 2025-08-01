#!/usr/bin/env python3
"""
Test script for the Nutrition A2A Agent functionality
"""
import asyncio
import json
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import NutritionAgentExecutor

async def test_nutrition_agent():
    """Test the Nutrition Agent with various queries"""
    print("🧪 Testing Nutrition A2A Agent")
    print("=" * 50)
    
    try:
        # Create the agent
        agent = NutritionAgentExecutor()
        print("✅ Agent created successfully")
        
        # Test queries
        test_queries = [
            "What are the calories in an apple?",
            "Show me nutrition info for 1 cup rice",
            "How much protein is in chicken breast?",
            "Tell me about pizza nutrition",
            "Hello, what can you do?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 40)
            
            # Simulate the data structure the agent expects
            test_data = {"message": query}
            
            try:
                result = await agent._process_request(test_data)
                print("📊 Result:")
                print(json.dumps(result, indent=2))
                
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
        
        print(f"\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Failed to create agent: {str(e)}")
        return

if __name__ == "__main__":
    asyncio.run(test_nutrition_agent())