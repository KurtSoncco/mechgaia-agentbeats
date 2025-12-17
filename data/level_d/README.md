# Level D Tasks: Multi-Component System Design

Level D tasks require agents to design multi-component mechanical systems with multiple constraints, design variables, and objectives. These tasks test the agent's ability to:

1. Select materials and geometric parameters for multiple components
2. Perform system-level analysis (deflections, stresses, frequencies, etc.)
3. Satisfy multiple constraints simultaneously
4. Optimize designs while respecting constraints
5. Write executable code to verify designs

## Task Overview

### 1. `level_d_two_span_1.json` - Two-Span Continuous Beam System

**Objective**: Design a continuous two-span beam system with different cross-sections and materials for each span, optimizing for natural frequency while satisfying deflection, stress, and mass constraints.

**Key Features**:
- Two spans with independent material and section choices
- Multi-objective optimization (frequency vs. mass)
- Serviceability constraints (deflection, stress, frequency)

**Approximations Used**:
- Simplified beam deflection formulas (superposition for continuous beams)
- Equivalent single-degree-of-freedom frequency approximation
- Series spring model for combined system stiffness

**Constraint Interpretation**:
- Deflection constraints use simplified beam formulas
- Frequency uses effective mass and equivalent stiffness
- Small deviations (±5%) acceptable due to approximation differences

---

### 2. `level_d_frame_1.json` - Two-Story Portal Frame

**Objective**: Design a two-story, single-bay portal frame under lateral and gravity loads. Choose member sizes and materials to satisfy drift, stress, and frequency constraints while controlling total mass.

**Key Features**:
- Multi-story structural system
- Combined lateral and gravity loading
- Dynamic response (natural frequency) consideration

**Approximations Used**:
- Simplified column stiffness: `k_story = 2 * 12 * E * I_col / H^3` (two columns)
- Lumped lateral loads at floor levels
- Fixed-fixed beam approximation for gravity loads
- Cantilever model for column bending from lateral loads
- Effective mass approximation: `m_eff ≈ 0.8 * total_mass`

**Constraint Interpretation**:
- Story drift uses simplified stiffness method
- Beam deflection uses standard beam formulas
- Frequency uses equivalent SDOF approximation
- Mass calculations include all members (columns + beams)

---

### 3. `level_d_cost_beam_1.json` - Cost-Optimal Simply Supported Beam

**Objective**: Select material and rectangular cross-section for a simply supported beam to satisfy deflection, stress, and frequency constraints while minimizing cost.

**Key Features**:
- Material selection with cost considerations
- Multi-material comparison (Steel, Aluminum, Composite)
- Cost optimization objective

**Approximations Used**:
- Standard beam deflection: `delta = 5wL^4 / (384EI)`
- Simply supported beam frequency: `k_eq ≈ 48EI / L^3`
- Effective mass: `m_eff ≈ 0.5 * m`

**Constraint Interpretation**:
- Deflection uses Euler-Bernoulli beam theory
- Frequency uses equivalent stiffness method
- Cost = mass × cost_per_kg
- Reference design may slightly exceed cost budget to demonstrate trade-offs

---

### 4. `level_d_shaft_system_1.json` - Two-Segment Shaft Torsion and Bending Design

**Objective**: Design a two-segment shaft transmitting torque to a gear and pulley system. Choose shaft diameters and materials to satisfy torsional shear, bending stress, twist, and mass constraints.

**Key Features**:
- Combined torsion and bending loading
- Multiple load locations (gear and pulley)
- Twist angle constraint

**Approximations Used**:
- Standard torsion formulas: `tau = Tr/J`, `theta = TL/(GJ)`
- Bending stress at discrete load points
- Independent segment analysis

**Constraint Interpretation**:
- Torsional shear uses maximum of both segments
- Bending stress checked at gear and pulley locations
- Total twist = sum of segment twists
- Mass = sum of segment masses

---

## Common Design Patterns

### Material Selection
- Level D tasks often include material options (e.g., Steel S235 vs S355, Steel vs Aluminum)
- Material properties affect stiffness, strength, density, and cost
- Agents must balance these trade-offs

### Constraint Satisfaction
- Multiple constraints must be satisfied simultaneously
- Some constraints may conflict (e.g., minimizing mass vs. maximizing frequency)
- Agents should aim to satisfy all constraints, with small deviations (±5%) acceptable due to approximations

### Code Requirements
- All Level D tasks require executable Python code
- Code should compute system metrics (deflections, stresses, frequencies, masses)
- Code should be self-contained and use standard libraries (math)

### Verification
- Each task has a corresponding `*_verifier.py` file
- Verifiers recompute metrics using simplified formulas
- Reference answers are validated against verifiers
- Small differences between reference and verifier outputs are expected due to approximation differences

---

## Usage

### Loading Tasks
```python
from src.mechgaia_env.task_generator import TaskGenerator
from src.mechgaia_env.database import BenchmarkDatabase

db = BenchmarkDatabase()
generator = TaskGenerator(db)
generator.generate_level_d_tasks(examples_dir="data/level_d/examples")
```

### Running Verifiers
```bash
cd data/level_d/examples
uv run python level_d_two_span_1_verifier.py
```

### Running Tests
```bash
uv run python tests/test_level_d_examples.py
```

---

## Notes for Evaluators

1. **Approximation Tolerance**: Reference designs use simplified formulas. Verifiers use similar but potentially different approximations. Small metric differences (±10-15%) are acceptable.

2. **Constraint Satisfaction**: Reference designs aim to satisfy constraints, but may have minor violations due to approximation differences. Constraint thresholds are set to accommodate these differences.

3. **Code Execution**: The primary evaluation criterion is that code executes and produces reasonable results. Exact metric matching is secondary.

4. **Design Rationale**: Agents should provide clear rationale for design choices, explaining trade-offs between objectives and constraints.

5. **Multi-Step Process**: Level D tasks require multiple steps (material selection, geometry design, analysis, verification). Agents should demonstrate understanding of this process.
