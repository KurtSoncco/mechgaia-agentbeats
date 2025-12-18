"""White agent implementation - the target agent being tested."""

import os
import sys
import tomllib

import dotenv
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils import new_agent_text_message
from litellm import completion

dotenv.load_dotenv()


def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)


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

5. **For Design Problems (Level C)**:
   - Use tools to perform calculations and evaluate design options
   - After completing your analysis, you MUST output exactly one fenced code block tagged ```json
   - The content of that block MUST be a single JSON object with the following structure:
     {
       "design": {
         "height_m": <float>,
         "frequency_Hz": <float>,
         "deflection_m": <float>,
         "mass_kg": <float>,
         "max_stress_MPa": <float>,
         "safety_factor": <float>
       },
       "rationale": "<string: 2-6 sentences explaining key trade-offs and whether constraints are met>",
       "code": "<string: valid Python code that recomputes the design metrics from first principles>"
     }
   - Do not include any additional text before or after the ```json code block
   - Do not wrap the JSON in markdown list items or quotes
   - If you conclude that no feasible design exists within the specified variable bounds and material properties, still output the JSON object, but set "design" to your best attempt and clearly state in "rationale" that the constraints are mutually incompatible
   
   **Example Output Format (for reference - use different numbers in your actual response):**
   ```json
   {
     "design": {
       "height_m": 0.18,
       "frequency_Hz": 42.3,
       "deflection_m": 0.0015,
       "mass_kg": 3.2,
       "max_stress_MPa": 65.8,
       "safety_factor": 3.8
     },
     "rationale": "Selected height of 0.18 m to balance frequency and mass constraints. The design meets deflection and stress requirements but falls slightly short of the 50 Hz frequency target due to material limitations.",
     "code": "import math\nL = 1.0\nb = 0.05\nh = 0.18\nE = 210e9\nrho = 7850.0\nP = 100.0\nA = b * h\nm = rho * A * L\nI = b * h**3 / 12\nDelta = P * L**3 / (3 * E * I)\nM_max = P * L\nc = h / 2.0\nsigma = M_max * c / I\nsigma_MPa = sigma / 1e6\nsigma_y = 250.0\nSF = sigma_y / sigma_MPa\nf = (1.875**2 / (2 * math.pi * L**2)) * math.sqrt(E * I / (rho * A))\nprint({'height_m': h, 'frequency_Hz': f, 'deflection_m': Delta, 'mass_kg': m, 'max_stress_MPa': sigma_MPa, 'safety_factor': SF})"
   }
   ```

6. **For Multi-Step Design Problems (Level D)**:
   - Use tools to perform calculations for each step (material selection, serviceability checks, system evaluation)
   - After completing all steps, you MUST output exactly one fenced code block tagged ```json
   - The content of that block MUST be a single JSON object with the following structure:
     {
       "design": {
         "span_1": {"material": "<string>", "height_m": <float>},
         "span_2": {"material": "<string>", "height_m": <float>}
       },
       "system_metrics": {
         "max_deflection_m": <float>,
         "max_stress_span_1_MPa": <float>,
         "max_stress_span_2_MPa": <float>,
         "min_frequency_Hz": <float>,
         "total_mass_kg": <float>
       },
       "rationale": "<string: 2-6 sentences explaining multi-step decisions and system-level trade-offs>",
       "code": "<string: valid Python code that computes system metrics from first principles>"
     }
   - Do not include any additional text before or after the ```json code block
   - Ensure your design addresses all steps and system-level constraints

**OUTPUT FORMAT (MANDATORY)**

For Level C and Level D tasks, you MUST follow this exact format:

1. **Level C Output Schema:**
   - Keys: "design" (dict), "rationale" (string), "code" (string)
   - "design" must contain: height_m, frequency_Hz, deflection_m, mass_kg, max_stress_MPa, safety_factor (all floats)
   - "rationale" must be a string (2-6 sentences)
   - "code" must be valid Python code as a string

2. **Level D Output Schema:**
   - Keys: "design" (dict), "system_metrics" (dict), "rationale" (string), "code" (string)
   - "design" must contain span_1 and span_2, each with material (string) and height_m (float)
   - "system_metrics" must contain: max_deflection_m, max_stress_span_1_MPa, max_stress_span_2_MPa, min_frequency_Hz, total_mass_kg (all floats)
   - "rationale" must be a string (2-6 sentences)
   - "code" must be valid Python code as a string

3. **Critical Requirements:**
   - ALWAYS wrap your JSON output in ```json code fences
   - ALWAYS output exactly ONE JSON object (not multiple)
   - ALWAYS include ALL required keys
   - NEVER output text before or after the JSON block
   - If you cannot complete a field, use reasonable defaults (e.g., 0.0 for floats, "" for strings)

**Example Level C Output:**
```json
{
  "design": {
    "height_m": 0.20,
    "frequency_Hz": 45.2,
    "deflection_m": 0.0018,
    "mass_kg": 3.5,
    "max_stress_MPa": 58.3,
    "safety_factor": 4.3
  },
  "rationale": "Selected height of 0.20 m to optimize frequency while meeting all constraints.",
  "code": "import math\n# ... your code here ..."
}
```

7. **Always**: 
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
    agent_card_dict = load_agent_card_toml(agent_name)

    # Debug: Print environment variables
    print("[DEBUG] Environment variables:", file=sys.stderr)
    print(
        f"  AGENT_URL_WHITE: {os.getenv('AGENT_URL_WHITE', 'not set')}", file=sys.stderr
    )
    print(f"  AGENT_URL: {os.getenv('AGENT_URL', 'not set')}", file=sys.stderr)
    print(f"  CLOUDRUN_HOST: {os.getenv('CLOUDRUN_HOST', 'not set')}", file=sys.stderr)
    print(f"  HTTPS_ENABLED: {os.getenv('HTTPS_ENABLED', 'not set')}", file=sys.stderr)
    print(f"  HOST: {os.getenv('HOST', 'not set')}", file=sys.stderr)
    print(f"  PORT: {os.getenv('PORT', 'not set')}", file=sys.stderr)

    # Determine agent URL: prioritize AGENT_URL (set by controller), then AGENT_URL_WHITE, then construct from CLOUDRUN_HOST
    agent_url = os.getenv("AGENT_URL") or os.getenv("AGENT_URL_WHITE")

    if agent_url:
        print(
            f"[DEBUG] Using agent_url: {agent_url}",
            file=sys.stderr,
        )

    # If AGENT_URL is not set, try to construct from CLOUDRUN_HOST
    if not agent_url:
        cloudrun_host = os.getenv("CLOUDRUN_HOST")
        if cloudrun_host:
            https_enabled = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
            protocol = "https" if https_enabled else "http"
            agent_url = f"{protocol}://{cloudrun_host}"
            print(
                f"[DEBUG] Constructed agent_url from CLOUDRUN_HOST: {agent_url}",
                file=sys.stderr,
            )

    if agent_url:
        # Strip trailing slashes to prevent double slashes
        # Note: /to_agent/<agent-id> path handling is done by earthshaker/controller
        # We preserve the full URL as-is (including /to_agent/ paths) and just remove trailing slashes
        agent_card_url = agent_url.rstrip("/")
        print(f"[DEBUG] Using agent_card_url: {agent_card_url}", file=sys.stderr)
    else:
        # Default to localhost for local development
        agent_card_url = f"http://{host}:{port}"
        print(f"[DEBUG] Using default localhost URL: {agent_card_url}", file=sys.stderr)

    print(f"[DEBUG] Final agent_card URL: {agent_card_url}", file=sys.stderr)
    agent_card_dict["url"] = agent_card_url

    request_handler = DefaultRequestHandler(
        agent_executor=GeneralWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
