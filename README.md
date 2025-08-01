# A2A Agent Template

Template for building A2A-compatible agents using Google's Agent-to-Agent SDK.

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py
```

## Development

Customize your agent by modifying the `_process_request` method in `main.py`:

```python
async def _process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # Your custom agent logic goes here
    message = data.get("message", "No message provided")
    
    result = {
        "status": "success",
        "processed_message": f"Processed: {message}",
        "agent": "TemplateAgent"
    }
    return result
```

## Agent Structure

- **AgentCard**: Defines agent metadata, capabilities, and skills
- **AgentExecutor**: Handles incoming requests and processes them
- **RequestContext**: Contains the incoming message and metadata
- **EventQueue**: Used to send responses back to the requesting agent

## Deployment

The `app` variable exposes an A2AStarletteApplication instance for platform deployment.

## Resources

- [Google A2A Samples](https://github.com/a2aproject/a2a-samples) - Official A2A sample implementations
- [A2A Python SDK Documentation](https://github.com/a2aproject/A2A) - Core A2A protocol and Python SDK
- [Google ADK Python](https://github.com/google/adk-python) - Agent Development Kit for building sophisticated AI agents


