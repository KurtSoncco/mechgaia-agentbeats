import asyncio
import uuid

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    TextPart,
)

from src.mechgaia_env.config import config


async def get_agent_card(url: str) -> AgentCard | None:
    # Configure timeout for agent card retrieval
    # Normalize URL to prevent double slashes when A2ACardResolver adds paths
    # Strip trailing slashes first
    url = url.rstrip("/")
    # If URL contains /to_agent/ path, we need to handle it specially
    # The agent card should be accessible at the base URL with /.well-known/agent-card.json
    # So we extract just the base domain + protocol
    if "/to_agent/" in url:
        # Extract base URL (protocol + domain) up to /to_agent/
        # This handles routing paths added by deployment infrastructure
        parts = url.split("/to_agent/")
        base_url = parts[0]
        url = base_url.rstrip("/")
    timeout = httpx.Timeout(
        connect=config.a2a_connect_timeout,
        read=config.a2a_timeout,
        write=config.a2a_timeout,
        pool=config.a2a_connect_timeout,
    )
    httpx_client = httpx.AsyncClient(timeout=timeout)
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)

    card: AgentCard | None = await resolver.get_agent_card()

    return card


async def wait_agent_ready(url, timeout=10):
    # wait until the A2A server is ready, check by getting the agent card
    retry_cnt = 0
    while retry_cnt < timeout:
        retry_cnt += 1
        try:
            card = await get_agent_card(url)
            if card is not None:
                return True
            else:
                print(
                    f"Agent card not available yet..., retrying {retry_cnt}/{timeout}"
                )
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def send_message(
    url, message, task_id=None, context_id=None
) -> SendMessageResponse:
    card = await get_agent_card(url)
    # Configure timeout with separate values for connect, read, write, and pool
    # Use longer timeouts for agent operations that may take time to process
    timeout = httpx.Timeout(
        connect=config.a2a_connect_timeout,
        read=config.a2a_timeout,
        write=config.a2a_timeout,
        pool=config.a2a_connect_timeout,
    )
    httpx_client = httpx.AsyncClient(timeout=timeout)
    client = A2AClient(httpx_client=httpx_client, agent_card=card)

    message_id = uuid.uuid4().hex
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=message))],
            message_id=message_id,
            task_id=task_id,
            context_id=context_id,
        )
    )
    request_id = uuid.uuid4().hex
    req = SendMessageRequest(id=request_id, params=params)
    response = await client.send_message(request=req)
    return response
