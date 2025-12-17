#!/usr/bin/env python
"""AgentBeats controller for MechGaia agents."""

import sys
import tomllib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="MechGaia Controller")

# Agent configurations
# White agent runs on port 9003, controller uses 9002
AGENTS = {
    "white": {
        "id": "af71be80-9702-43c2-b9f8-d95dda16e63a",
        "name": "MechGaia White Agent",
        "url": "http://localhost:9003",  # White agent runs on 9003
        "type": "assessee",
        "status": "healthy",
    },
    "green": {
        "id": "green-agent-uuid",
        "name": "MechGaia Green Agent",
        "url": "http://localhost:9001",
        "type": "assessor",
        "status": "healthy",
    },
}


# Load white agent card from TOML to ensure it matches
def load_white_agent_card():
    """Load white agent card from TOML file."""
    toml_path = (
        Path(__file__).parent / "src" / "white_agent" / "mechgaia_white_agent.toml"
    )
    with toml_path.open("rb") as f:
        config = tomllib.load(f)

    # Parse capabilities
    capabilities_config = config.get("capabilities", {})
    capabilities = {"streaming": capabilities_config.get("streaming", False)}

    # Parse skills (include examples if present)
    skills = []
    for skill_config in config.get("skills", []):
        skill_dict = {
            "id": skill_config.get("id", ""),
            "name": skill_config.get("name", ""),
            "description": skill_config.get("description", ""),
            "tags": skill_config.get("tags", []),
        }
        # Include examples if present (white agent card has examples: [])
        if "examples" in skill_config:
            skill_dict["examples"] = skill_config.get("examples", [])
        skills.append(skill_dict)

    # Build controller card matching white agent card
    # For AgentBeats v2, we should present as the white agent itself, not as a controller
    controller_card = {
        "name": config.get("name", "MechGaia White Agent"),
        "description": config.get(
            "description", "MechGaia mechanical engineering solver"
        ),
        "version": config.get("version", "0.1.0"),
        "url": "https://white.mechgaia.org",
        "capabilities": capabilities,
        "defaultInputModes": config.get("defaultInputModes", ["text"]),
        "defaultOutputModes": config.get("defaultOutputModes", ["text"]),
        "protocolVersion": "0.3.0",
        "preferredTransport": "JSONRPC",
        "skills": skills,
        # Note: managedAgents is controller-specific metadata, but AgentBeats v2
        # might not recognize controllers. We present as the white agent directly.
        # Uncomment if AgentBeats v2 supports controller pattern:
        # "managedAgents": [
        #     {
        #         "id": agent["id"],
        #         "name": agent["name"],
        #         "type": agent["type"],
        #         "url": agent["url"],
        #     }
        #     for agent in AGENTS.values()
        # ],
    }
    return controller_card


CONTROLLER_CARD = load_white_agent_card()

# ============================================================================
# Agent Card Endpoints
# ============================================================================


@app.get("/.well-known/agent-card.json")
async def agent_card_get():
    """Get controller agent card via GET."""
    return JSONResponse(CONTROLLER_CARD)


@app.post("/.well-known/agent-card.json")
async def agent_card_post():
    """Get controller agent card via POST."""
    return JSONResponse(CONTROLLER_CARD)


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/health")
async def health():
    """Health check endpoint - returns white agent health."""
    target_agent = AGENTS["white"]

    # Check white agent health
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{target_agent['url']}/health")
            if response.status_code == 200:
                health_data = response.json()
                # Return health as if we are the white agent
                return {
                    "status": "healthy",
                    "ready": health_data.get("ready", True),
                }
    except Exception:
        pass

    # Fallback if white agent check fails
    return {
        "status": "healthy",
        "ready": True,
    }


@app.get("/info")
async def info():
    """Controller info endpoint - AgentBeats expects type='controller'.

    AgentBeats controller will check YOURDOMAIN/info (https://white.mechgaia.org/info)
    not localhost, so this endpoint must be accessible via Cloudflare.
    """
    return {
        "agent_id": "af71be80-9702-43c2-b9f8-d95dda16e63a",
        "name": "MechGaia White Agent",
        "type": "controller",  # AgentBeats controller expects this
        "status": "healthy",
        "managed_agents": list(AGENTS.keys()),
        "version": "0.1.0",
        "url": "https://white.mechgaia.org",  # Public URL for AgentBeats
    }


# ============================================================================
# Agent Management Endpoints
# ============================================================================


@app.get("/agents")
async def list_agents():
    """List all managed agents."""
    return {
        "agents": [
            {
                "id": agent["id"],
                "name": agent["name"],
                "type": agent["type"],
                "url": agent["url"],
                "status": agent["status"],
            }
            for agent in AGENTS.values()
        ]
    }


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get specific agent info."""
    if agent_name not in AGENTS:
        return JSONResponse({"error": f"Agent {agent_name} not found"}, status_code=404)

    agent = AGENTS[agent_name]
    return {
        "id": agent["id"],
        "name": agent["name"],
        "type": agent["type"],
        "url": agent["url"],
        "status": agent["status"],
    }


@app.get("/agents/{agent_name}/health")
async def agent_health(agent_name: str):
    """Check specific agent health."""
    if agent_name not in AGENTS:
        return JSONResponse({"error": f"Agent {agent_name} not found"}, status_code=404)

    agent = AGENTS[agent_name]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{agent['url']}/health")
            if response.status_code == 200:
                return {
                    "agent": agent_name,
                    "status": "healthy",
                    "details": response.json(),
                }
    except Exception as e:
        return {"agent": agent_name, "status": "unhealthy", "error": str(e)}


# ============================================================================
# A2A Message Proxy Endpoints
# ============================================================================


@app.api_route(
    "/a2a/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy_a2a(request: Request, path: str):
    """Proxy all A2A requests to white agent."""
    target_agent = AGENTS["white"]
    target_url = f"{target_agent['url']}/a2a/{path}"

    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except Exception:
            try:
                body = await request.body()
            except Exception:
                pass

    # Get query parameters
    params = dict(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            # Prepare request kwargs
            request_kwargs = {
                "method": request.method,
                "url": target_url,
                "params": params,
                "headers": {
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in ["host", "content-length", "connection"]
                },
            }

            # Add body if present
            if body:
                if isinstance(body, dict):
                    request_kwargs["json"] = body
                else:
                    request_kwargs["content"] = body

            # Forward the request
            response = await client.request(**request_kwargs)

            # Return response
            response_text = response.text
            content_type = response.headers.get("content-type", "")

            # Check for empty response
            if not response_text or not response_text.strip():
                print(
                    f"Empty response from white agent (status {response.status_code})"
                )
                return JSONResponse(
                    content={"error": "White agent returned empty response"},
                    status_code=502,
                )

            if "application/json" in content_type or response_text.strip().startswith(
                "{"
            ):
                try:
                    return JSONResponse(
                        content=response.json(),
                        status_code=response.status_code,
                    )
                except Exception as json_err:
                    print(f"Failed to parse JSON response: {json_err}")
                    print(f"Response text (first 500 chars): {response_text[:500]}")
                    return JSONResponse(
                        content={
                            "error": f"Invalid JSON response from white agent: {str(json_err)}"
                        },
                        status_code=502,
                    )
            else:
                from fastapi.responses import Response

                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    media_type=content_type,
                )
    except httpx.TimeoutException:
        return JSONResponse(
            {"error": "Timeout waiting for white agent response"}, status_code=504
        )
    except httpx.ConnectError:
        return JSONResponse(
            {
                "error": f"Failed to connect to white agent at {target_agent['url']}. Is it running?"
            },
            status_code=502,
        )
    except Exception as e:
        import traceback

        print(f"Proxy error: {traceback.format_exc()}")
        return JSONResponse(
            {"error": f"Failed to proxy request: {str(e)}"}, status_code=502
        )


# ============================================================================
# Root & Discovery Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint returns agent card."""
    return JSONResponse(CONTROLLER_CARD)


@app.post("/")
async def root_post(request: Request):
    """Handle POST requests to root - proxy to white agent's root endpoint."""
    target_agent = AGENTS["white"]
    target_url = f"{target_agent['url']}/"  # A2A SDK uses root endpoint

    try:
        body = await request.json()
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    print(f"Proxying POST / to white agent at {target_url}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Proxy to white agent's root endpoint (A2A SDK uses JSON-RPC on root)
            response = await client.post(target_url, json=body)
            print(f"White agent responded with status {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(
                f"Response content type: {response.headers.get('content-type', 'unknown')}"
            )

            # Handle response based on content type
            response_text = response.text
            content_type = response.headers.get("content-type", "").lower()

            # Check for empty response
            if not response_text or not response_text.strip():
                print(
                    f"Empty response from white agent (status {response.status_code})"
                )
                return JSONResponse(
                    {"error": "White agent returned empty response"}, status_code=502
                )

            if "application/json" in content_type or response_text.strip().startswith(
                "{"
            ):
                try:
                    return JSONResponse(
                        response.json(), status_code=response.status_code
                    )
                except Exception as json_err:
                    print(f"Failed to parse JSON response: {json_err}")
                    print(f"Response text (first 500 chars): {response_text[:500]}")
                    print(f"Response length: {len(response_text)}")
                    return JSONResponse(
                        {
                            "error": f"Invalid JSON response from white agent: {str(json_err)}"
                        },
                        status_code=502,
                    )
            else:
                # Non-JSON response
                print(f"Non-JSON response: {response_text[:500]}")
                return JSONResponse(
                    {
                        "error": f"White agent returned non-JSON response: {response_text[:200]}"
                    },
                    status_code=502,
                )
    except httpx.TimeoutException as e:
        print(f"Timeout connecting to white agent: {e}")
        return JSONResponse(
            {"error": "Timeout waiting for white agent response"}, status_code=504
        )
    except httpx.ConnectError as e:
        print(f"Connection error to white agent at {target_url}: {e}")
        return JSONResponse(
            {
                "error": f"Failed to connect to white agent at {target_url}. Is it running?"
            },
            status_code=502,
        )
    except httpx.HTTPStatusError as e:
        print(f"HTTP error from white agent: {e}")
        try:
            error_body = e.response.json()
        except Exception:
            error_body = {"error": f"HTTP {e.response.status_code}"}
        return JSONResponse(error_body, status_code=e.response.status_code)
    except Exception as e:
        import traceback

        print(f"Unexpected error proxying to white agent: {traceback.format_exc()}")
        return JSONResponse(
            {"error": f"Failed to proxy message: {str(e)}"}, status_code=502
        )


@app.get("/discovery")
async def discovery():
    """Service discovery endpoint."""
    return {
        "type": "controller",
        "name": "MechGaia Controller",
        "agents": list(AGENTS.keys()),
        "endpoints": {
            "agent_card": "/.well-known/agent-card.json",
            "health": "/health",
            "agents": "/agents",
            "messages": "/a2a/messages",
        },
    }


# ============================================================================
# Startup & Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize controller on startup."""
    print("=" * 60)
    print("🚀 MechGaia Controller Starting")
    print("=" * 60)
    print(f"Managing {len(AGENTS)} agents:")
    for name, agent in AGENTS.items():
        print(f"  - {name}: {agent['name']} ({agent['url']})")
    print()
    print("Available endpoints:")
    print("  Agent Card: /.well-known/agent-card.json")
    print("  Health: /health")
    print("  Agents: /agents")
    print("  Messages: /a2a/messages")
    print()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\n🛑 MechGaia Controller Shutting Down")


# ============================================================================
# CLI Entry Point
# ============================================================================


def start_controller(host="0.0.0.0", port=9002):
    """Start the controller (defaults to port 9002 for white.mechgaia.org)."""
    print(f"Starting MechGaia Controller on {host}:{port}")
    print(f"Controller will proxy to white agent at {AGENTS['white']['url']}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MechGaia Controller")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()
    start_controller(args.host, args.port)
