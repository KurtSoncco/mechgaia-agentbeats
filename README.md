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

## Architecture Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Launcher  │────────▶│ Green Agent  │────────▶│White Agent  │
│  (orchestrates) │     │ (Evaluator)  │         │ (LLM being  │
│             │         │              │         │  tested)    │
└─────────────┘         └──────────────┘         └─────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │   Database   │
                        │  (Results)   │
                        └──────────────┘
```


**Note:** If `AGENT_URL_GREEN` or `AGENT_URL_WHITE` are not set, the agents will automatically default to `http://localhost:{port}` based on the port they're running on.

## Usage

### Launch Complete Evaluation

The launcher will start both agents and run a MechGAIA evaluation:

```bash
# Launch complete evaluation (starts both agents and runs test)
# If no levels are specified, all available levels in the database will be evaluated
uv run python main.py launch

# Run a specific level (A, B, C, or D)
uv run python main.py launch --level A
# or using short form
uv run python main.py launch -l A

# Run multiple levels
uv run python main.py launch --levels A,B,C
```

**Level Options:**
- `--level` / `-l`: Run a single task level (A, B, C, or D)
- `--levels`: Run multiple levels as comma-separated values (e.g., `A,B,C`)
- If neither option is specified, all available levels in the database will be automatically detected and evaluated

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
# Basic remote evaluation
uv run python main.py launch_remote <green_url> <white_url>

# Remote evaluation with specific level(s)
uv run python main.py launch_remote <green_url> <white_url> --level A
uv run python main.py launch_remote <green_url> <white_url> --levels A,B,C

# Remote evaluation with custom model
uv run python main.py launch_remote <green_url> <white_url> --model openai/gpt-4o
```

## Testing

The project includes a comprehensive test suite using pytest. Run tests with:

```bash
# Run all tests
uv run pytest tests/

# Run tests with verbose output
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/test_schema_validation.py

# Run a specific test
uv run pytest tests/test_schema_validation.py::test_level_a_schema_validation
```

**Test Coverage:**
- Schema validation for all levels (A, B, C, D)
- Numeric verifiers for Level B/C/D tasks
- JSON parsing and response extraction
- Level D example validation
- White agent output parsing

## MechGAIA Environment

The framework uses the MechGAIA benchmark environment (`env: "mechgaia"`), which provides:
- Mechanical engineering problem scenarios
- Scientific computing tools (calculator, Python scipy, numpy, etc.)
- Simple problems initially (more complex problems can be added later)

The green agent instantiates MechGAIA to test the white agent's ability to solve mechanical engineering problems using the available tools.
