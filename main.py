import os
import json
import uvicorn

from typing import Dict, Any

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


class TemplateAgentExecutor(AgentExecutor):
    """A2A Agent Executor template for building agent-to-agent applications."""

    def __init__(self):
        super().__init__()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute method required by AgentExecutor interface."""
        try:
            # Extract task information from context
            message_parts = context.message.parts if context.message else []
            task_data = {}
            task_type = "process_request"

            # Parse message content to extract task type and data
            if message_parts and len(message_parts) > 0:
                if hasattr(message_parts[0], "text"):
                    try:
                        # Try to parse as JSON for structured requests
                        parsed_data = json.loads(message_parts[0].text)
                        task_type = parsed_data.get("task_type", "process_request")
                        task_data = parsed_data.get("data", {})
                    except (json.JSONDecodeError, AttributeError):
                        # Handle as plain text request
                        task_data = {"message": message_parts[0].text}

            # Process the task
            result = await self._handle_task(task_type, task_data)

            await event_queue.enqueue_event(
                new_agent_text_message(json.dumps(result, indent=2))
            )

        except Exception as e:
            await event_queue.enqueue_event(new_agent_text_message(f"Error: {str(e)}"))

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())

    async def _handle_task(
        self, task_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle different task types - customize this method for your agent."""
        if task_type == "process_request":
            return await self._process_request(data)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def _process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Template implementation - replace with your agent logic."""
        message = data.get("message", "No message provided")

        # Your custom agent logic goes here
        result = {
            "status": "success",
            "processed_message": f"Processed: {message}",
            "timestamp": "2024-01-01T00:00:00Z",
            "agent": "TemplateAgent",
        }

        return result


# Create agent card
agent_card = AgentCard(
    name="TemplateAgent",
    description="A2A agent template for building custom agents",
    version="1.0.0",
    url=os.getenv("HU_APP_URL") or "",  # Provide empty string as fallback
    capabilities=AgentCapabilities(
        streaming=True, push_notifications=False, state_transition_history=True
    ),
    skills=[
        AgentSkill(
            id="process_request",
            name="Process Request",
            description="Process incoming requests and return processed responses",
            tags=["template", "processing", "a2a"],
            examples=["Process user input", "Handle data requests"],
            input_modes=["application/json", "text/plain"],
            output_modes=["application/json", "text/plain"],
        )
    ],
    default_input_modes=["application/json", "text/plain"],
    default_output_modes=["application/json", "text/plain"],
    provider=AgentProvider(
        organization="Your Organization",
        url="https://www.healthuniverse.com",
    ),
)

# Create the A2A Starlette application
agent_executor = TemplateAgentExecutor()

request_handler = DefaultRequestHandler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
)
app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler).build()

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
