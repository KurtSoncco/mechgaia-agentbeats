# MechGAIA Benchmark Results
Comprehensive evaluation report with detailed metrics across all task levels.
---
## Executive Summary
| Level | Tasks | Instances | Avg Primary Score | Avg Success Rate |
|-------|-------|-----------|-------------------|------------------|
| A | 5 | 21 | 0.500 | 28.6% |
| B | 2 | 43 | 0.698 | 69.8% |
| C | 1 | 29 | 0.624 | 72.4% |
| D | 1 | 2 | 0.650 | 50.0% |

---

## Level A Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| Linear vs Nonlinear Elasticity | openai/gpt-4o | 0.300 | 0.0% | 5 | [0.100, 0.500] |
| Yield vs Ultimate Strength | openai/gpt-4o | 0.500 | 25.0% | 4 | [0.125, 0.875] |
| Fatigue Mechanisms | openai/gpt-4o | 0.375 | 0.0% | 4 | [0.125, 0.500] |
| Fracture Modes | openai/gpt-4o | 0.625 | 50.0% | 4 | [0.250, 1.000] |
| Failure Criteria | openai/gpt-4o | 0.750 | 75.0% | 4 | [0.250, 1.000] |

### Detailed Metrics Breakdown
| Task | Model | technical_accuracy | conceptual_clarity | distractor_analysis | reasoning_quality | overall_score |
|------|-------|---|---|---|---|---|
| Linear vs Nonlinear Elasticity | openai/gpt-4o | 1.000 | 0.640 | 0.480 | 1.000 | 0.867 |
| Yield vs Ultimate Strength | openai/gpt-4o | 1.000 | 0.650 | 0.400 | 0.800 | 0.800 |
| Fatigue Mechanisms | openai/gpt-4o | 1.000 | 0.800 | 0.500 | 1.000 | 0.800 |
| Fracture Modes | openai/gpt-4o | 1.000 | 0.800 | 0.500 | 1.000 | 0.867 |
| Failure Criteria | openai/gpt-4o | 1.000 | 0.750 | 0.450 | 0.800 | 0.800 |

---

## Level B Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| Euler-Bernoulli Beam Deflection | openai/gpt-4o | 0.654 | 65.4% | 26 | [0.462, 0.808] |
| Axial Bar Extension | openai/gpt-4o | 0.765 | 76.5% | 17 | [0.529, 0.941] |

### Detailed Metrics Breakdown
| Task | Model | value_tolerance | unit_consistency | code_execution | mej_technical_accuracy | mej_mathematical_rigor | mej_problem_solving_approach | mej_engineering_judgment | mej_overall_score |
|------|-------|---|---|---|---|---|---|---|---|
| Euler-Bernoulli Beam Deflection | openai/gpt-4o | 0.708 | 0.500 | 0.462 | 0.256 | 0.296 | 0.216 | 0.224 | 0.240 |
| Axial Bar Extension | openai/gpt-4o | 0.765 | 0.882 | 0.500 | 0.824 | 0.824 | 0.447 | 0.671 | 0.682 |

---

## Level C Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| Cantilever Beam Frequency Optimization | openai/gpt-4o | 0.624 | 72.4% | 29 | [0.564, 0.681] |

### Detailed Metrics Breakdown
| Task | Model | technical_accuracy | safety_constraint_awareness | reasoning_quality | engineering_judgment |
|------|-------|---|---|---|---|
| Cantilever Beam Frequency Optimization | openai/gpt-4o | 0.634 | 0.731 | 0.572 | 0.600 |

---

## Level D Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| Two-span continuous beam system design | openai/gpt-4o | 0.650 | 50.0% | 2 | [0.400, 0.900] |

### Detailed Metrics Breakdown
| Task | Model | technical_accuracy | multi_step_coordination | system_constraint_awareness | engineering_judgment |
|------|-------|---|---|---|---|
| Two-span continuous beam system design | openai/gpt-4o | 0.600 | 0.800 | 0.700 | 0.700 |

---

