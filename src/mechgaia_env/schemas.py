"""Pydantic schemas for MechGAIA benchmark tasks."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LevelATask(BaseModel):
    """Level A task schema - multiple choice fundamentals."""

    id: str
    topic: str
    question: str
    options: List[str] = Field(..., min_length=2)
    correct_option: int = Field(..., ge=0)
    rubric_explanation_points: Dict[str, int] = Field(
        default_factory=dict,
        description="Points for addressing each explanation requirement",
    )
    distractor_analysis: List[str] = Field(
        default_factory=list, description="Required analysis for each distractor option"
    )


class LevelBTask(BaseModel):
    """Level B task schema - parametric calculations."""

    id: str
    topic: str
    problem_template: str
    symbolic_variables: Dict[str, str] = Field(
        description="Variable names and their descriptions"
    )
    units: Dict[str, str] = Field(description="Units for each variable")
    ground_truth_formula: str = Field(description="Formula string (Python-compatible)")
    reference_solution: float = Field(description="Reference solution value")
    tolerance: float = Field(default=0.01, ge=0)
    parameter_ranges: Dict[str, Dict[str, float]] = Field(
        description="Ranges for parameter sampling: {var: {min, max}}"
    )


class LevelCTask(BaseModel):
    """Level C task schema - design & optimization."""

    id: str
    topic: str
    objectives: List[str] = Field(
        description="Design objectives (e.g., minimize mass, maximize frequency)"
    )
    constraints: List[str] = Field(
        description="Design constraints (e.g., deflection < 10mm, stress < yield)"
    )
    design_variables: Dict[str, Dict[str, Any]] = Field(
        description="Design variables with ranges and types"
    )
    reference_design: Dict[str, Any] = Field(description="Reference design parameters")
    material_options: List[str] = Field(
        default_factory=list, description="Available material options"
    )
    evaluation_criteria: Dict[str, float] = Field(
        default_factory=dict, description="Criteria weights or thresholds"
    )


class LevelDTask(BaseModel):
    """Level D task schema - multi-component / multi-step design tasks."""

    id: str
    level: str = Field(default="D", description="Task level")
    type: str = Field(
        description="Task type (e.g., 'multi_component_beam', 'frame', 'material_co_design')"
    )
    title: str = Field(description="Task title")
    description: str = Field(description="Task description")
    steps: List[Dict[str, Any]] = Field(
        description="List of steps, each with name, description, design_variables, constraints, etc."
    )
    given: Dict[str, Any] = Field(
        default_factory=dict,
        description="Given parameters (geometry, loads, materials)",
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="System-level constraints"
    )
    objectives: List[str] = Field(default_factory=list, description="Design objectives")
    expected_output_schema: Dict[str, Any] = Field(
        description="Expected output schema with design, system_metrics, rationale, code"
    )
    material_options: List[Dict[str, Any]] = Field(
        default_factory=list, description="Available material options with properties"
    )


class TaskInstance(BaseModel):
    """Instance of a task with specific parameters."""

    id: str
    task_id: str
    level: str = Field(..., pattern="^[ABCD]$")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    gold_answer: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evaluation(BaseModel):
    """Evaluation result for a task instance."""

    id: str
    task_instance_id: str
    model_name: str
    response: Dict[str, Any] = Field(default_factory=dict)
    scores: Dict[str, float] = Field(default_factory=dict)
    timestamp: Optional[str] = None
