<div align="center">

# 🚀 MechGaia AgentBeats

**A standardized agent assessment framework for evaluating AI agents on mechanical engineering problems**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![A2A](https://img.shields.io/badge/A2A-0.3.8+-orange.svg)](https://github.com/a2a-sdk)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

Built using **A2A (Agent-to-Agent)** and **MCP (Model Context Protocol)** standards, this framework tests agents' ability to solve engineering problems using scientific computing tools (calculator, Python scipy, numpy, etc.).

---

### 🎯 Quick Actions

<a href="#quick-start"><img src="https://img.shields.io/badge/🚀 Quick Start-Get Started-blue?style=for-the-badge" alt="Quick Start"></a>
<a href="#installation"><img src="https://img.shields.io/badge/📦 Installation-Setup-green?style=for-the-badge" alt="Installation"></a>
<a href="#task-levels"><img src="https://img.shields.io/badge/📊 Task Levels-View Details-orange?style=for-the-badge" alt="Task Levels"></a>
<a href="#usage"><img src="https://img.shields.io/badge/💻 Usage-Examples-purple?style=for-the-badge" alt="Usage"></a>

---

</div>

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Task Levels](#task-levels)
- [Evaluation Process](#evaluation-process)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 📖 Overview

MechGaia AgentBeats evaluates AI agents on their ability to solve mechanical engineering problems across **four difficulty levels (A through D)**. The framework uses a distributed agent architecture where:

<div align="center">

| Component | Role | Description |
|-----------|------|-------------|
| 🟢 **Green Agent** | Assessment Manager | Hosts the MechGAIA benchmark, presents tasks, and evaluates responses |
| ⚪ **White Agent** | Target Agent | The agent being tested (typically an LLM-powered agent) |
| 🚀 **Launcher** | Orchestrator | Orchestrates the evaluation workflow, starting agents and coordinating the assessment |

</div>

### ✨ Key Features

- ✅ **Quantitative Evaluation**: Unit tests, constraint satisfaction, numerical accuracy
- ✅ **Qualitative Evaluation**: LLM-as-Judge scoring for comprehensive assessment
- ✅ **Multi-Level Testing**: Four progressive difficulty levels (A → D)
- ✅ **Scientific Computing**: Integration with Python scipy, numpy, and engineering tools
- ✅ **Automated Reporting**: Statistical analysis and result visualization

## 🏗️ Architecture

### System Components

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

<div align="center">

**🔄 Communication Flow**

</div>

### Key Definitions

- **Green Agent**: The evaluator/assessor agent that manages the benchmark, presents tasks to the white agent, and evaluates responses using both automated tests and LLM-as-Judge scoring.

- **White Agent**: The agent being tested. It receives engineering problems and must solve them using available tools (calculator, Python execution, etc.). The white agent communicates via A2A protocol.

- **Task**: A mechanical engineering problem with a specific schema and objectives. Tasks are stored in a SQLite database.

- **Task Instance**: A specific instantiation of a task with particular parameters. Each task can have multiple instances with different parameter values.

- **Level**: Task difficulty classification (A, B, C, or D) representing increasing complexity:
  - **Level A**: Multiple-choice conceptual questions
  - **Level B**: Parametric calculation problems
  - **Level C**: Single-component design optimization
  - **Level D**: Multi-component system design

- **Evaluation**: The process of presenting a task to the white agent, collecting its response, and scoring it using quantitative (unit tests) and qualitative (LLM-as-Judge) methods.

## 📦 Installation

### Prerequisites

<div align="center">

| Requirement | Version | Notes |
|-------------|---------|-------|
| 🐍 **Python** | 3.13+ | Required |
| 📦 **uv** | Latest | Recommended package manager |
| 🔄 **pip** | Latest | Alternative to uv |

</div>

### Setup

<details>
<summary><b>📋 Step-by-Step Installation Guide</b></summary>

#### 1️⃣ Clone the repository:
```bash
git clone <repository-url>
cd mechgaia-agentbeats
```

#### 2️⃣ Install dependencies:
```bash
uv sync
```

#### 3️⃣ Set up environment variables (see [Configuration](#configuration))

</details>

<div align="center">

**⚡ Quick Install**

```bash
git clone <repository-url> && cd mechgaia-agentbeats && uv sync
```

</div>

## 🚀 Quick Start

<div align="center">

**Get up and running in 4 simple steps!**

</div>

### Step 1: Generate Tasks (One-time Setup)

<div align="center">

<details>
<summary><b>📝 Click to expand task generation commands</b></summary>

</div>

Before running evaluations, you need to populate the database with tasks:

```bash
# Generate tasks for all levels
python scripts/generate_tasks.py generate --level A --num-tasks 5 --num-instances 10
python scripts/generate_tasks.py generate --level B --num-tasks 5 --num-instances 10
python scripts/generate_tasks.py generate --level C --num-tasks 3 --num-instances 10

# Level D tasks are loaded from example files
python scripts/generate_tasks.py generate --level D --examples-dir data/level_d/examples
```

</details>

### Step 2: Set Environment Variables

<div align="center">

<details>
<summary><b>🔐 Click to expand environment configuration</b></summary>

</div>

Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
# Both green and white agents use the same API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: for litellm proxy
LITELLM_PROXY_API_KEY=your-proxy-key

# Optional: Agent URL Configuration (defaults to localhost if not set)
AGENT_URL_GREEN=http://localhost:9001
AGENT_URL_WHITE=http://localhost:9002
```

</details>

### Step 3: Run the Benchmark

<div align="center">

**Choose your preferred method:**

</div>

<details>
<summary><b>✅ Option A: All-in-one (Recommended for First Time)</b></summary>

This automatically starts both agents and runs the evaluation:

```bash
# Default: Runs one instance of Level C for testing
uv run python main.py launch

# Run a specific level
uv run python main.py launch --level A

# Run multiple levels
uv run python main.py launch --levels A,B,C
```

</details>

<details>
<summary><b>⚙️ Option B: Manual (For Production/Testing)</b></summary>

**Terminal 1** - Start Green Agent (Evaluator):
```bash
uv run python main.py green
```

**Terminal 2** - Start White Agent (LLM being tested):
```bash
uv run python main.py white
```

**Terminal 3** - Run Evaluation:
```bash
# Evaluate Level A tasks
uv run python main.py launch_remote http://localhost:9001 http://localhost:9002 --level A

# Evaluate Level B tasks  
uv run python main.py launch_remote http://localhost:9001 http://localhost:9002 --level B

# Evaluate specific model
uv run python main.py launch_remote http://localhost:9001 http://localhost:9002 --level A --model "anthropic/claude-3-opus"
```

</details>

### Step 4: View Results

<div align="center">

```bash
# Generate reports
python scripts/analyze_results.py analyze --output-dir results

# View markdown report
cat results/report.md
```

</div>

## 📊 Task Levels

<div align="center">

**The framework evaluates agents across four progressively challenging levels:**

| Level | Type | Complexity | Focus |
|-------|------|------------|-------|
| **A** | Multiple-Choice | ⭐ Basic | Conceptual Understanding |
| **B** | Parametric Calculation | ⭐⭐ Intermediate | Numerical Problem Solving |
| **C** | Single-Component Design | ⭐⭐⭐ Advanced | Design Optimization |
| **D** | Multi-Component System | ⭐⭐⭐⭐ Expert | System-Level Design |

</div>

### 📝 Level A: Multiple-Choice Conceptual Questions

<div align="center">

**⭐ Basic Level - Conceptual Understanding**

</div>

<details>
<summary><b>📋 View Details</b></summary>

**Description**: Tests fundamental understanding of mechanical engineering concepts through multiple-choice questions.

**Characteristics**:
- ✅ Conceptual understanding questions
- ✅ No calculations required
- ✅ Focus on engineering principles and theory
- ✅ Requires explanation and distractor analysis

**Example Topics**:
- 🔬 Material properties and behavior
- 📐 Stress and strain concepts
- 🏗️ Beam theory fundamentals
- ⚡ Vibration and dynamics principles

**Response Format**: Agent selects an option and provides reasoning.

**Evaluation Criteria**:
- ✅ **Correctness** (binary: correct/incorrect option selection)
- 📊 **Technical Accuracy** (1-5): Correct understanding of engineering concepts
- 📝 **Conceptual Clarity** (1-5): Clear and well-structured explanation
- 🔍 **Distractor Analysis** (1-5): Explanation of why selected option is correct and others are wrong
- 🧠 **Reasoning Quality** (1-5): Sound engineering reasoning and logical thought process

</details>

### 🔢 Level B: Parametric Calculation Problems

<div align="center">

**⭐⭐ Intermediate Level - Numerical Problem Solving**

</div>

<details>
<summary><b>📋 View Details</b></summary>

**Description**: Tests ability to perform engineering calculations with given parameters.

**Characteristics**:
- 🔢 Numerical problems with specific input parameters
- 🛠️ Requires tool usage (calculator, Python execution)
- 📐 Focus on correct application of formulas
- 📏 Unit handling and conversion

**Example Topics**:
- 📊 Beam deflection calculations
- ⚙️ Stress analysis
- 🌊 Natural frequency computation
- 🔬 Material property calculations

**Response Format**: Agent provides numerical answer, optionally with code and explanation.

**Evaluation Criteria**:

**Quantitative (UnitTestGrader)**:
- ✅ **Correctness**: Numerical accuracy within ±1% tolerance
- ✅ **Value Tolerance**: Pass/fail based on ±1% error threshold
- ✅ **Unit Consistency**: Proper unit handling and conversion
- ✅ **Code Execution**: Successful execution of provided code
- ✅ **Intermediate Logic**: Correct calculation steps

**Qualitative (LLMJudgeGrader)**:
- 📊 **Technical Accuracy** (1-5): Correct governing equations and sound physics
- 🧮 **Mathematical Rigor** (1-5): Accurate calculations and proper unit handling
- 🎯 **Problem-Solving Approach** (1-5): Logical and well-structured solution method
- 🏗️ **Engineering Judgment** (1-5): Physically reasonable results and engineering context awareness

</details>

### 🎯 Level C: Single-Component Design Optimization

<div align="center">

**⭐⭐⭐ Advanced Level - Design Optimization**

</div>

<details>
<summary><b>📋 View Details</b></summary>

**Description**: Tests ability to design and optimize a single mechanical component with multiple constraints.

**Characteristics**:
- 🎨 Design optimization problems
- 🔒 Multiple constraints (deflection, stress, frequency, mass)
- 📐 Requires selecting design variables (geometry, material)
- 💻 Must provide executable code to verify design

**Example Topics**:
- 🏗️ Beam design (height, width, material selection)
- 🌊 Frequency optimization
- ✅ Constraint satisfaction
- ⚖️ Trade-off analysis

**Response Format**: Agent provides:
- 📋 Design parameters (JSON object with geometric and material choices)
- 📝 Rationale (2-6 sentences explaining trade-offs)
- 💻 Executable Python code to recompute design metrics

**Evaluation Criteria**:

**Quantitative**:
- ✅ **Constraint Satisfaction**: All constraints met (deflection, stress, frequency, mass)
- ✅ **Code Execution**: Code runs successfully and produces expected outputs
- ✅ **Syntax Correctness**: Valid Python syntax

**Qualitative (LLMJudgeGrader)**:
- 📊 **Technical Accuracy** (1-5): Correct identification of key relationships (e.g., f₁ ∝ √(EI/(ρAL⁴)))
- 🛡️ **Safety/Constraint Awareness** (1-5): Addresses safety factors, manufacturing constraints, cost
- 🧠 **Reasoning Quality** (1-5): Explains design choices and scaling relationships
- 🏗️ **Engineering Judgment** (1-5): Practical, manufacturable design with considered trade-offs

</details>

### 🏗️ Level D: Multi-Component System Design

<div align="center">

**⭐⭐⭐⭐ Expert Level - System-Level Design**

</div>

<details>
<summary><b>📋 View Details</b></summary>

**Description**: Tests ability to design multi-component mechanical systems with complex interactions.

**Characteristics**:
- 🔗 Multi-component systems (e.g., two-span beams, frames, shaft systems)
- 📊 System-level analysis (deflections, stresses, frequencies across components)
- 📐 Multiple design variables per component
- 🎨 Material selection and geometry optimization
- 🔒 System-level constraints

**Example Topics**:
- 🌉 Two-span continuous beam systems
- 🏢 Multi-story portal frames
- ⚙️ Shaft systems with multiple segments
- 💰 Cost-optimal designs

**Response Format**: Agent provides:
- 📋 Design parameters for all components
- 📊 System metrics (deflections, stresses, frequencies, masses)
- 📝 Rationale explaining multi-step decision-making
- 💻 Executable Python code for system verification

**Evaluation Criteria**:

**Quantitative**:
- ✅ **System Constraint Satisfaction**: All system-level constraints met
- ✅ **Code Execution**: Code executes and produces system metrics
- ✅ **Component Coordination**: Consistent design across components

**Qualitative (LLMJudgeGrader)**:
- 📊 **Technical Accuracy** (1-5): Correct handling of multi-component interactions
- 🔗 **Multi-Step Coordination** (1-5): All steps addressed, consistent decisions
- 🎯 **System Constraint Awareness** (1-5): System-level constraints properly addressed
- 🏗️ **Engineering Judgment** (1-5): Practical system design with well-reasoned trade-offs

> **⚠️ Note**: Level D tasks use simplified engineering formulas. Small metric differences (±10-15%) between reference and verifier outputs are acceptable due to approximation differences.

</details>

## 🔄 Evaluation Process

### 📋 Workflow

<div align="center">

**7-step evaluation workflow**

</div>

1. **📝 Task Selection**: The launcher determines which tasks to evaluate based on:
   - ✅ Explicit level specification (`--level` or `--levels`)
   - ✅ Default behavior: one instance of Level C (for testing)
   - ✅ Database contents (auto-detects available levels)

2. **🚀 Agent Initialization**:
   - 🟢 Green agent starts on port 9001
   - ⚪ White agent starts on port 9002
   - ✅ Both agents register and become ready

3. **📋 Task Presentation**:
   - 🗄️ Green agent loads task from database
   - 📝 Presents problem statement to white agent
   - 🛠️ Provides available tools (calculator, Python execution, etc.)

4. **💬 Agent Response**:
   - 🤖 White agent solves problem using tools
   - 📊 Responds with answer, code, and/or explanation
   - 📐 Format depends on task level (see [Task Levels](#task-levels))

5. **✅ Evaluation**:
   - **🔢 Quantitative Evaluation**: UnitTestGrader checks:
     - ✅ Numerical correctness (within tolerance)
     - ✅ Code execution success
     - ✅ Constraint satisfaction
   
   - **📊 Qualitative Evaluation**: LLMJudgeGrader (Mechanical Engineering Judge) scores:
     - 📐 Technical accuracy
     - 🧮 Mathematical rigor
     - 🏗️ Engineering judgment
     - 🧠 Reasoning quality

6. **💾 Result Storage**:
   - 🗄️ Scores stored in SQLite database (`data/benchmark.db`)
   - 📊 Results include: task ID, instance ID, model name, scores, timestamps

7. **📈 Report Generation**:
   - 📊 Use `scripts/analyze_results.py` to generate statistical reports
   - 📈 Reports include mean scores, confidence intervals, per-level breakdowns

### 📊 Scoring Methodology

<div align="center">

**Two-pronged evaluation approach**

</div>

**🔢 Quantitative Scoring**:
- Level B: ±1% tolerance for numerical answers
- Level C/D: Binary constraint satisfaction (met/not met)
- Code execution: Pass/fail based on successful execution

**📊 Qualitative Scoring**:
- LLM-as-Judge (Mechanical Engineering Judge) evaluates responses
- Scores range from 1-5 for each criterion
- Normalized to 0-1 scale for aggregation
- Considers: technical accuracy, mathematical rigor, constraint awareness, engineering judgment

**📈 Final Scores**:
- Per-instance scores stored in `evaluations` table
- Aggregated scores (mean, CI) stored in `results` table
- Reports generated with statistical analysis

## 💻 Usage

### 🚀 Launch Complete Evaluation

<div align="center">

**The launcher will start both agents and run a MechGAIA evaluation**

</div>

```bash
# Launch complete evaluation
# Default: Runs one instance of Level C for testing
uv run python main.py launch

# Run a specific level (A, B, C, or D)
uv run python main.py launch --level A
# or using short form
uv run python main.py launch -l A

# Run multiple levels
uv run python main.py launch --levels A,B,C
```

<div align="center">

| Option | Short Form | Description |
|--------|------------|-------------|
| `--level` | `-l` | Run a single task level (A, B, C, or D) |
| `--levels` | - | Run multiple levels as comma-separated values (e.g., `A,B,C`) |
| *(none)* | - | Defaults to one instance of Level C for testing |

</div>

### 🔄 Run Agents Separately

<div align="center">

**You can also run the agents separately for more control**

</div>

```bash
# Start green agent (assessment manager) on port 9001
uv run python main.py green

# Start white agent (target being tested) on port 9002
uv run python main.py white
```

### 🌐 Remote Evaluation

<div align="center">

**If you have agents running remotely**

</div>

```bash
# Basic remote evaluation
uv run python main.py launch_remote <green_url> <white_url>

# Remote evaluation with specific level(s)
uv run python main.py launch_remote <green_url> <white_url> --level A
uv run python main.py launch_remote <green_url> <white_url> --levels A,B,C

# Remote evaluation with custom model
uv run python main.py launch_remote <green_url> <white_url> --model openai/gpt-4o
```

### 📝 Task Generation

<div align="center">

**Generate tasks for evaluation**

</div>

```bash
# Generate Level A tasks
python scripts/generate_tasks.py generate --level A --num-tasks 5 --num-instances 10

# Generate Level B tasks
python scripts/generate_tasks.py generate --level B --num-tasks 5 --num-instances 10

# Generate Level C tasks
python scripts/generate_tasks.py generate --level C --num-tasks 3 --num-instances 10

# Load Level D tasks from examples
python scripts/generate_tasks.py generate --level D --examples-dir data/level_d/examples
```

### 📊 Result Analysis

<div align="center">

**Generate reports from evaluation results**

</div>

```bash
# Analyze results and generate report
python scripts/analyze_results.py analyze --output-dir results

# View markdown report
cat results/report.md

# View JSON results
cat results/results.jsonl
```

## ⚙️ Configuration

### 🔐 Environment Variables

<div align="center">

**Create a `.env` file in the project root**

</div>

```bash
# OpenAI API Configuration
# Both green and white agents use the same API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: for litellm proxy
LITELLM_PROXY_API_KEY=your-proxy-key

# Optional: Agent URL Configuration (defaults to localhost if not set)
AGENT_URL_GREEN=http://localhost:9001
AGENT_URL_WHITE=http://localhost:9002
```

> **💡 Note**: If `AGENT_URL_GREEN` or `AGENT_URL_WHITE` are not set, the agents will automatically default to `http://localhost:{port}` based on the port they're running on.

### 🗄️ Database Configuration

<div align="center">

**Tasks and results are stored in SQLite database**

</div>

| Setting | Value |
|---------|-------|
| **Default Location** | `data/benchmark.db` |
| **Tables** | `tasks`, `task_instances`, `evaluations`, `results` |

**Table Descriptions**:
- 📋 `tasks`: Task definitions (schema, level, topic)
- 🔢 `task_instances`: Specific task instantiations with parameters
- ✅ `evaluations`: Individual evaluation results
- 📊 `results`: Aggregated scores per task

### 🤖 Agent Configuration

<div align="center">

| Agent | Configuration File |
|-------|-------------------|
| 🟢 **Green Agent** | `src/green_agent/mechgaia_green_agent.toml` |
| ⚪ **White Agent** | `src/white_agent/general_white_agent.toml` |

</div>

## 🧪 Testing

<div align="center">

**The project includes a comprehensive test suite using pytest**

</div>

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

<div align="center">

**Test Coverage**

</div>

| Test Area | Coverage |
|-----------|----------|
| ✅ Schema validation | All levels (A, B, C, D) |
| 🔢 Numeric verifiers | Level B/C/D tasks |
| 📋 JSON parsing | Response extraction |
| 🏗️ Level D examples | Example validation |
| 🤖 White agent | Output parsing |

## 🔧 Troubleshooting

### ❌ Common Issues

<details>
<summary><b>🔍 "No tasks found"</b></summary>

**Solution**:
- Run `scripts/generate_tasks.py` first to populate the database
- Check that `data/benchmark.db` exists and contains tasks

</details>

<details>
<summary><b>🔌 "Connection refused"</b></summary>

**Solution**:
- Make sure both agents are running
- Check ports 9001 (green) and 9002 (white) are available
- Verify firewall settings if running remotely

</details>

<details>
<summary><b>🔑 "API key error"</b></summary>

**Solution**:
- Set `OPENAI_API_KEY` environment variable
- Create `.env` file in project root with your API key
- Verify API key is valid and has sufficient credits

</details>

<details>
<summary><b>📋 "No Level C tasks found"</b></summary>

**Solution**:
- Generate Level C tasks: `python scripts/generate_tasks.py generate --level C --num-tasks 3 --num-instances 10`
- Check database: `sqlite3 data/benchmark.db "SELECT * FROM tasks WHERE level='C';"`

</details>

<details>
<summary><b>⏱️ "Agent not ready in time"</b></summary>

**Solution**:
- Increase timeout in `src/my_util/my_a2a.py` if agents are slow to start
- Check agent logs for startup errors
- Verify dependencies are installed correctly

</details>

<details>
<summary><b>💻 "Code execution failed"</b></summary>

**Solution**:
- Check white agent's code output format
- Verify Python code syntax is correct
- Check sandbox executor logs for execution errors

</details>

### 🐛 Debugging Tips

<div align="center">

**Helpful debugging strategies**

</div>

1. **📋 Check Agent Logs**: Both agents print detailed logs to console
2. **🗄️ Database Inspection**: Use SQLite to inspect tasks and results:
   ```bash
   sqlite3 data/benchmark.db
   .tables
   SELECT * FROM tasks LIMIT 5;
   SELECT * FROM evaluations LIMIT 5;
   ```
3. **🔬 Test Individual Components**: Run agents separately to isolate issues
4. **✅ Verify Environment**: Ensure all dependencies are installed (`uv sync`)

## 📁 Project Structure

<div align="center">

**Project organization and key directories**

</div>

```
src/
├── green_agent/          # 🟢 Assessment manager agent (hosts MechGAIA benchmark)
│   ├── agent.py          # Green agent implementation
│   └── mechgaia_green_agent.toml  # Agent configuration
├── white_agent/          # ⚪ Target agent being tested
│   ├── agent.py          # White agent implementation
│   └── general_white_agent.toml    # Agent configuration
├── launcher.py           # 🚀 Evaluation coordinator
├── mechgaia_env/         # 🏗️ MechGAIA environment implementation
│   ├── database.py       # Database operations
│   ├── evaluators.py     # Scoring and evaluation logic
│   ├── env.py            # Environment interface
│   ├── task_generator.py # Task generation
│   └── ...
└── my_util/              # 🛠️ Utility functions
    └── my_a2a.py         # A2A communication helpers

scripts/
├── generate_tasks.py     # 📝 Task generation script
├── analyze_results.py    # 📊 Result analysis script
└── ...

data/
├── benchmark.db          # 🗄️ SQLite database (tasks and results)
├── level_c/              # Level C task examples
├── level_d/              # Level D task examples
└── materials.json        # 🔬 Material properties database

tests/                    # 🧪 Test suite
results/                  # 📊 Evaluation results and reports
```

## 🏗️ MechGAIA Environment

<div align="center">

**The framework uses the MechGAIA benchmark environment (`env: "mechgaia"`)**

</div>

### ✨ Features

| Feature | Description |
|---------|-------------|
| 📋 **Problem Scenarios** | Realistic engineering problems across multiple difficulty levels |
| 🛠️ **Scientific Computing Tools** | Calculator, Python scipy, numpy, material database, plotting tools |
| 🗄️ **Task Management** | Database-backed task storage and retrieval |
| ✅ **Evaluation Framework** | Automated quantitative and qualitative scoring |

### 🛠️ Available Tools

- 🔢 **Calculator**: Basic arithmetic operations
- 🐍 **Python scipy**: Scientific computing
- 📊 **Python numpy**: Numerical operations
- 🔬 **Material Database**: Engineering properties
- 📈 **Plotting Tools**: Stress-strain and other diagrams

> The green agent instantiates MechGAIA to test the white agent's ability to solve mechanical engineering problems using the available tools.

## 🎯 Key Points

<div align="center">

**Quick reference guide**

</div>

| Component | Description |
|-----------|-------------|
| 🟢 **Green Agent** | Evaluator/Assessor (manages benchmark, evaluates responses) |
| ⚪ **White Agent** | Agent Being Tested (the LLM that solves tasks) |
| 🗄️ **Database** | Tasks stored in SQLite (`data/benchmark.db`) |
| 📊 **Results** | Evaluated and stored automatically |
| 📈 **Reports** | Use `scripts/analyze_results.py` to generate statistical reports |
| 🚀 **Default Launch** | Runs one instance of Level C for quick testing |
| 📋 **Level Specification** | Explicit level evaluates all instances for that level |

---

## 📄 License

<div align="center">

[Add license information here]

</div>

## 🤝 Contributing

<div align="center">

[Add contributing guidelines here]

**We welcome contributions!** Please feel free to submit a Pull Request.

</div>

## 📚 Citation

<div align="center">

[Add citation information here]

</div>

---

<div align="center">

**Made with ❤️ for the Mechanical Engineering AI Community**

[⬆ Back to Top](#mechgaia-agentbeats)

</div>
