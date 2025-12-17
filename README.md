# MechGaia AgentBeats

MechGaia agent assessment framework using A2A and MCP standards. This framework evaluates agents on mechanical engineering problems using scientific computing tools (calculator, Python scipy, numpy, etc.).

## Project Structure

```
src/
├── green_agent/    # Assessment manager agent (hosts MechGAIA benchmark)
├── white_agent/    # Target agent being tested
└── launcher.py     # Evaluation coordinator
```

## Installation

```bash
uv sync
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (you can copy from `.env.example`):

```bash
# OpenAI API Configuration
# Both green and white agents use the same API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Agent URL Configuration (optional - defaults to localhost if not set)
AGENT_URL_GREEN=http://localhost:9001
AGENT_URL_WHITE=http://localhost:9002
```

**Note:** If `AGENT_URL_GREEN` or `AGENT_URL_WHITE` are not set, the agents will automatically default to `http://localhost:{port}` based on the port they're running on.

## Usage

### Launch Complete Evaluation

The launcher will start both agents and run a MechGAIA evaluation:

```bash
# Launch complete evaluation (starts both agents and runs test)
uv run python main.py launch
```

### Run Agents Separately

You can also run the agents separately:

```bash
# Start green agent (assessment manager) on port 9001
uv run python main.py green

# Start white agent (target being tested) on port 9002
uv run python main.py white
```

### Remote Evaluation

If you have agents running remotely:

```bash
uv run python main.py launch-remote <green_url> <white_url>
```

## MechGAIA Environment

The framework uses the MechGAIA benchmark environment (`env: "mechgaia"`), which provides:
- Mechanical engineering problem scenarios
- Scientific computing tools (calculator, Python scipy, numpy, etc.)
- Simple problems initially (more complex problems can be added later)

The green agent instantiates MechGAIA to test the white agent's ability to solve mechanical engineering problems using the available tools.
