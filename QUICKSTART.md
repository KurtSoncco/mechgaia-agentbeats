# Quick Start Guide

## Step-by-Step: Running the Benchmark

### 1. Generate Tasks (One-time setup)

```bash
# Generate tasks for all levels
python scripts/generate_tasks.py generate --level A --num-tasks 5 --num-instances 10
python scripts/generate_tasks.py generate --level B --num-tasks 5 --num-instances 10
python scripts/generate_tasks.py generate --level C --num-tasks 3 --num-instances 10
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
# Optional: for litellm proxy
export LITELLM_PROXY_API_KEY="your-proxy-key"
```

### 3. Run the Benchmark

**Option A: All-in-one (recommended for first time)**
```bash
python main.py launch
```

**Option B: Manual (for production/testing)**

Terminal 1 - Start Green Agent (Evaluator):
```bash
python main.py green
```

Terminal 2 - Start White Agent (LLM being tested):
```bash
python main.py white
```

Terminal 3 - Run Evaluation:
```bash
# Evaluate Level A tasks
python main.py launch-remote --level A

# Evaluate Level B tasks  
python main.py launch-remote --level B

# Evaluate specific model
python main.py launch-remote --level A --model "anthropic/claude-3-opus"
```

### 4. View Results

```bash
# Generate reports
python scripts/analyze_results.py analyze --output-dir results

# View markdown report
cat results/report.md
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

## Key Points

- **Green Agent** = Evaluator/Assessor (manages benchmark, evaluates responses)
- **White Agent** = Agent Being Tested (the LLM that solves tasks)
- Tasks are stored in SQLite database (`data/benchmark.db`)
- Results are evaluated and stored automatically
- Use `analyze_results.py` to generate statistical reports

## Troubleshooting

**"No tasks found"**: Run `generate_tasks.py` first
**"Connection refused"**: Make sure both agents are running
**"API key error"**: Set `OPENAI_API_KEY` environment variable
