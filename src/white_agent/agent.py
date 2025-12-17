"""White agent implementation - the target agent being tested."""

import os

import dotenv
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from litellm import completion

dotenv.load_dotenv()


def prepare_white_agent_card(url):
    skill = AgentSkill(
        id="task_fulfillment",
        name="Task Fulfillment",
        description="Handles user requests and completes tasks",
        tags=["general"],
        examples=[],
    )
    card = AgentCard(
        name="general_white_agent",
        description="A general-purpose white agent for task fulfillment.",
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
    )
    return card


class GeneralWhiteAgentExecutor(AgentExecutor):
    def __init__(self):
        self.ctx_id_to_messages = {}
        self.system_prompt = """You are a mechanical engineering problem-solving assistant. Your task is to solve engineering problems step by step using the available tools.

IMPORTANT INSTRUCTIONS:
1. **Tool Usage Workflow**: Always use tools (calculator, python_exec) to solve problems before providing your final answer. Do NOT guess or provide answers without calculations.

2. **Response Format**: You must format your tool calls as JSON wrapped in <json>...</json> tags. Example:
   <json>
   {"name": "calculator", "kwargs": {"expression": "2 + 2"}}
   </json>
   
   Or to provide a final answer:
   <json>
   {"name": "respond", "kwargs": {"content": "The answer is 4.0 Pa."}}
   </json>

3. **For Calculation Problems (Level B)**:
   - Use calculator or python_exec to perform calculations
   - After getting results from tools, provide your final answer using the "respond" action
   - Your final response MUST clearly state the numerical answer (e.g., "The answer is 123.45 Pa" or "Result: 123.45")
   - Include both the numerical value and units in your final answer
   - Also include a brief explanation of your approach

4. **For Multiple Choice Problems (Level A)**:
   - Analyze the problem and options
   - Use tools if calculations are needed
   - Clearly state which option you select (e.g., "Option 1" or "The correct answer is Option 2")
   - Provide reasoning for your choice

5. **Always**: 
   - Use tools to verify your calculations
   - Provide clear, well-formatted responses
   - Include units in numerical answers
   - Show your work when possible"""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # parse the task
        user_input = context.get_user_input()
        if context.context_id not in self.ctx_id_to_messages:
            self.ctx_id_to_messages[context.context_id] = [
                {
                    "role": "system",
                    "content": self.system_prompt,
                }
            ]
        messages = self.ctx_id_to_messages[context.context_id]
        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        # Use OpenAI directly (litellm will automatically use OPENAI_API_KEY from environment)
        # Optionally support litellm_proxy if LITELLM_PROXY_API_KEY is set
        if os.environ.get("LITELLM_PROXY_API_KEY") is not None:
            response = completion(
                messages=messages,
                model="openrouter/openai/gpt-4o",
                custom_llm_provider="litellm_proxy",
                temperature=0.0,
            )
        else:
            # Default to OpenAI - requires OPENAI_API_KEY environment variable
            response = completion(
                messages=messages,
                model="openai/gpt-4o",
                custom_llm_provider="openai",
                temperature=0.0,
            )
        next_message = response.choices[0].message.model_dump()  # type: ignore
        messages.append(
            {
                "role": "assistant",
                "content": next_message["content"],
            }
        )
        await event_queue.enqueue_event(
            new_agent_text_message(
                next_message["content"], context_id=context.context_id
            )
        )

    async def cancel(self, context, event_queue) -> None:
        raise NotImplementedError


def start_white_agent(agent_name="general_white_agent", host="localhost", port=9002):
    print("Starting white agent...")

    # Determine agent URL: check AGENT_URL_WHITE, then AGENT_URL, then default to localhost
    agent_url = os.getenv("AGENT_URL_WHITE") or os.getenv("AGENT_URL")
    if not agent_url:
        agent_url = f"http://{host}:{port}"
    card = prepare_white_agent_card(agent_url)

    request_handler = DefaultRequestHandler(
        agent_executor=GeneralWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
