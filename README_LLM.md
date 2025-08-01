# AI Nutrition Assistant - LLM-Powered A2A Agent

An intelligent nutrition analysis and meal planning assistant built with Google ADK and the A2A (Agent-to-Agent) framework. This agent provides personalized nutrition insights, meal analysis, and dietary recommendations using advanced AI capabilities.

## 🚀 Features

### Intelligence & Capabilities
- **LLM-Powered Responses**: Uses Google's Gemini 2.0 Flash model for intelligent, contextual responses
- **Real-time Nutrition Analysis**: Access to comprehensive nutrition database via Nutritionix API
- **Conversational Interface**: Natural language processing for intuitive interactions
- **Session Memory**: Maintains conversation context for personalized recommendations
- **Streaming Responses**: Real-time response generation for better user experience

### Nutrition Analysis
- **Individual Food Analysis**: Detailed nutritional breakdown of any food item
- **Meal Calculation**: Total nutrition analysis for complete meals
- **Personalized Recommendations**: AI-generated suggestions based on dietary goals
- **Comparative Analysis**: Side-by-side nutrition comparisons
- **Dietary Restriction Support**: Accommodates various dietary needs and health conditions

### Smart Features
- **Context-Aware Responses**: Understands dietary goals, restrictions, and preferences
- **Educational Content**: Provides nutrition science explanations and health guidance
- **Goal-Oriented Planning**: Meal suggestions tailored to specific health objectives
- **Multi-Modal Support**: Handles text queries and structured data

## 🏗️ Architecture

### Core Components

1. **LLM Nutrition Agent** (`llm_nutrition_agent.py`)
   - Google ADK integration with Gemini model
   - Session and memory management
   - Streaming response handling

2. **Nutrition Tools** (`nutrition_tools.py`)
   - Nutritionix API client
   - Food analysis functions
   - Meal calculation utilities
   - Recommendation engine

3. **A2A Integration** (`main_llm.py`)
   - Agent executor with streaming support
   - Task management and updates
   - Enhanced agent card configuration

### Technology Stack
- **AI Framework**: Google ADK (Agent Development Kit)
- **LLM**: Google Gemini 2.0 Flash
- **A2A Framework**: Agent-to-Agent communication protocol
- **Nutrition Data**: Nutritionix API
- **Backend**: Python with asyncio
- **Server**: Uvicorn/Starlette

## 📋 Prerequisites

### Required API Keys
1. **Google API Key**: For Gemini LLM access
   - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Required for intelligent responses and conversation capabilities

2. **Nutritionix API Key**: For comprehensive nutrition data
   - Get from [Nutritionix Developer Portal](https://developer.nutritionix.com/)
   - Used for accurate food nutrition analysis

### Environment Setup
Create a `.env` file with:
```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash-001
NUTRITIONIX_API_KEY=your_nutritionix_api_key_here
NUTRITIONIX_APP_ID=your_nutritionix_app_id_here
```

## 🛠️ Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your API keys

3. **Test the Agent**:
```bash
python test_llm_agent.py
```

4. **Start the Server**:
```bash
python main_llm.py
```

The server will be available at `http://localhost:8000`

## 🧪 Testing

### Quick Test
```bash
python test_llm_agent.py
```

This will run comprehensive tests including:
- Simple food analysis
- Complex meal analysis
- Personalized meal planning
- Comparative nutrition analysis
- Health condition specific advice

### Manual Testing Examples

**Simple Query**:
> "What are the calories in a large apple?"

**Complex Analysis**:
> "Analyze my breakfast: 2 scrambled eggs, 2 slices of whole wheat toast with butter, and a glass of orange juice"

**Personalized Planning**:
> "I'm trying to lose weight and need a high-protein, low-carb lunch suggestion under 400 calories"

**Health-Specific Advice**:
> "I'm diabetic and want to know if quinoa is a good rice substitute"

## 🔧 Configuration

### Model Selection
Change the LLM model in `.env`:
```env
GEMINI_MODEL=gemini-2.0-flash-001  # Fast, efficient
# or
GEMINI_MODEL=gemini-1.5-pro        # More capable, slower
```

### Logging
Adjust logging level in the main files:
```python
logging.basicConfig(level=logging.INFO)  # INFO, DEBUG, WARNING, ERROR
```

### Memory and Sessions
The agent automatically manages:
- **Session Persistence**: Conversations maintain context
- **Memory Management**: Relevant information is retained across interactions
- **Task Continuity**: Multi-turn conversations are supported

## 🔗 Integration

### A2A Agent Card
The agent exposes these skills:
- `intelligent_nutrition_analysis`: AI-powered food and meal analysis
- `meal_planning_assistant`: Personalized meal planning
- `nutrition_education`: Educational content and guidance

### Input/Output Modes
- **Input**: `text/plain`, `application/json`
- **Output**: `text/plain`, `application/json`
- **Capabilities**: Streaming, task history

## 🔍 Key Improvements Over Basic Version

### Intelligence
- **Contextual Understanding**: Interprets user intent and dietary context
- **Personalized Responses**: Tailors advice to individual needs and goals
- **Educational Value**: Explains nutritional concepts and health implications

### Functionality
- **Complex Query Handling**: Processes multi-food meals and comparative requests
- **Goal Integration**: Considers weight loss, muscle building, health conditions
- **Recommendation Engine**: Suggests foods, meals, and dietary changes

### User Experience
- **Natural Conversation**: Handles follow-up questions and clarifications
- **Streaming Responses**: Real-time feedback during processing
- **Error Recovery**: Graceful handling of unclear or incomplete queries

## 🐛 Troubleshooting

### Common Issues

1. **LLM Not Responding**:
   - Check `GOOGLE_API_KEY` is valid and set
   - Verify internet connection
   - Check API quotas and billing

2. **Nutrition Data Missing**:
   - Verify `NUTRITIONIX_API_KEY` configuration
   - Agent will fall back to mock data if API unavailable

3. **Import Errors**:
   - Ensure all dependencies installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

### Debug Mode
Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Notes

- **Response Time**: ~2-5 seconds for complex analyses
- **Streaming**: Updates appear in real-time during processing
- **Fallback**: Mock data used when APIs unavailable
- **Memory**: Session context maintained efficiently

## 🚀 Future Enhancements

- **Image Analysis**: Process food photos for nutrition analysis
- **Meal Planning**: Multi-day meal plan generation
- **Shopping Lists**: Generate grocery lists from meal plans
- **Health Integration**: Connect with fitness trackers and health apps
- **Recipe Suggestions**: Recommend recipes based on nutritional goals

---

This LLM-powered nutrition agent represents a significant advancement in AI-driven health and nutrition assistance, providing intelligent, personalized, and contextually aware responses to help users make better dietary decisions.