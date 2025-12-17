# MechGAIA Benchmark Results
Comprehensive evaluation report with detailed metrics across all task levels.
---

## Executive Summary
| Level | Tasks | Instances | Avg Primary Score | Avg Success Rate |
|-------|-------|-----------|-------------------|------------------|
| A | 5 | 21 | 0.510 | 60.0% |
| B | 2 | 43 | 0.709 | 100.0% |
| C | 1 | 0 | 0.000 | 0.0% |
| D | 1 | 0 | 0.000 | 0.0% |

---

## Level A Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| level_a_1 | openai/gpt-4o | 0.300 | 0.0% | 5 | [0.100, 0.500] |
| level_a_2 | openai/gpt-4o | 0.500 | 100.0% | 4 | [0.125, 0.875] |
| level_a_3 | openai/gpt-4o | 0.375 | 0.0% | 4 | [0.125, 0.500] |
| level_a_4 | openai/gpt-4o | 0.625 | 100.0% | 4 | [0.250, 1.000] |
| level_a_5 | openai/gpt-4o | 0.750 | 100.0% | 4 | [0.250, 1.000] |

### Detailed Metrics Breakdown
| Task | Model | conceptual_clarity | correctness | distractor_analysis | overall_reasoning | overall_score | reasoning_quality | technical_accuracy | technical_soundness |
|------|-------|---|---|---|---|---|---|---|---|
| level_a_1 | openai/gpt-4o | 0.200 | 0.000 | 0.200 | 0.200 | 0.000 | 0.000 | 0.000 | 0.200 |
| level_a_2 | openai/gpt-4o | 0.200 | 0.000 | 0.200 | 0.200 | 0.000 | 0.000 | 0.000 | 0.200 |
| level_a_3 | openai/gpt-4o | 0.200 | 0.000 | 0.200 | 0.200 | 0.000 | 0.000 | 0.000 | 0.200 |
| level_a_4 | openai/gpt-4o | 0.200 | 0.000 | 0.200 | 0.200 | 0.000 | 0.000 | 0.000 | 0.200 |
| level_a_5 | openai/gpt-4o | 0.200 | 0.000 | 0.200 | 0.200 | 0.000 | 0.000 | 0.000 | 0.200 |

---

## Level B Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| level_b_1 | openai/gpt-4o | 0.654 | 100.0% | 26 | [0.462, 0.808] |
| level_b_2 | openai/gpt-4o | 0.765 | 100.0% | 17 | [0.529, 0.941] |

### Detailed Metrics Breakdown
| Task | Model | absolute_error | code_execution | correctness | error | intermediate_logic | mej_engineering_judgment | mej_mathematical_rigor | mej_overall_score | mej_problem_solving_approach | mej_technical_accuracy | relative_error | unit_consistency | unit_conversion | value_tolerance |
|------|-------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| level_b_1 | openai/gpt-4o | 204.560 | 0.500 | 0.000 | 0.000 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1768967897801998336.000 | 0.500 | 0.000 | 0.000 |
| level_b_2 | openai/gpt-4o | 0.253 | 0.500 | 0.000 | 0.000 | 0.500 | 0.400 | 0.400 | 0.400 | 0.200 | 0.400 | 22.517 | 0.500 | 0.000 | 0.000 |

---

## Level C Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| level_c_1 | openai/gpt-4o | 0.000 | 0.0% | 0 | [0.000, 0.000] |

### Detailed Metrics Breakdown
| Task | Model | engineering_judgment | overall_score | reasoning_quality | safety_constraint_awareness | technical_accuracy |
|------|-------|---|---|---|---|---|
| level_c_1 | openai/gpt-4o | 0.400 | 0.400 | 0.400 | 0.600 | 0.400 |

---

## Level D Tasks
### Overall Statistics
| Task | Model | Primary Score | Success Rate | N | CI (95%) |
|------|-------|---------------|--------------|---|----------|
| level_d_two_span_1 | openai/gpt-4o | 0.000 | 0.0% | 0 | [0.000, 0.000] |

### Detailed Metrics Breakdown
| Task | Model | engineering_judgment | multi_step_coordination | overall_score | system_constraint_awareness | technical_accuracy |
|------|-------|---|---|---|---|---|
| level_d_two_span_1 | openai/gpt-4o | 0.800 | 1.000 | 0.900 | 1.000 | 0.800 |

---

## Summary Statistics

| Task ID | Model | Mean | CI Lower | CI Upper | N |
|---------|-------|------|----------|----------|---|
| level_a_1 | openai/gpt-4o | 0.300 | 0.100 | 0.500 | 5 |
| level_a_2 | openai/gpt-4o | 0.500 | 0.125 | 0.875 | 4 |
| level_a_3 | openai/gpt-4o | 0.375 | 0.125 | 0.500 | 4 |
| level_a_4 | openai/gpt-4o | 0.625 | 0.250 | 1.000 | 4 |
| level_a_5 | openai/gpt-4o | 0.750 | 0.250 | 1.000 | 4 |
| level_b_1 | openai/gpt-4o | 0.654 | 0.462 | 0.808 | 26 |
| level_b_2 | openai/gpt-4o | 0.765 | 0.529 | 0.941 | 17 |
| level_c_1 | openai/gpt-4o | 0.000 | 0.000 | 0.000 | 0 |
| level_d_two_span_1 | openai/gpt-4o | 0.000 | 0.000 | 0.000 | 0 |
