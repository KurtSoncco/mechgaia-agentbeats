"""Task generator for MechGAIA benchmark levels A, B, C, and D."""

import json
import random
from pathlib import Path

from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.schemas import LevelATask, LevelBTask, LevelCTask, LevelDTask


class TaskGenerator:
    """Generates tasks for different benchmark levels."""

    def __init__(self, db: BenchmarkDatabase):
        self.db = db

    def generate_level_a_tasks(self, num_tasks: int = 5):
        """Generate Level A tasks (fundamentals)."""
        templates = [
            {
                "topic": "Linear vs Nonlinear Elasticity",
                "question": "Which statement best describes the difference between linear and nonlinear elasticity?",
                "options": [
                    "Linear elasticity assumes constant Young's modulus, while nonlinear elasticity allows modulus to vary with strain",
                    "Linear elasticity only applies to metals, while nonlinear elasticity applies to polymers",
                    "Linear elasticity ignores Poisson's ratio, while nonlinear elasticity includes it",
                    "Linear and nonlinear elasticity are identical concepts with different names",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Explain why linear elasticity can apply to both metals and polymers",
                    "Clarify that Poisson's ratio is part of linear elasticity theory",
                    "Distinguish between linear/nonlinear elasticity and material types",
                ],
            },
            {
                "topic": "Yield vs Ultimate Strength",
                "question": "What is the key difference between yield strength and ultimate tensile strength?",
                "options": [
                    "Yield strength is the stress at which permanent deformation begins, while ultimate strength is the maximum stress before fracture",
                    "Yield strength applies only to compression, while ultimate strength applies to tension",
                    "Yield strength is always higher than ultimate strength",
                    "They are the same property measured at different temperatures",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Clarify that yield strength applies to both tension and compression",
                    "Explain that ultimate strength is typically higher than yield strength",
                    "Distinguish between strength properties and temperature effects",
                ],
            },
            {
                "topic": "Fatigue Mechanisms",
                "question": "What is the primary mechanism of fatigue failure in metals?",
                "options": [
                    "Progressive crack initiation and propagation under cyclic loading",
                    "Sudden brittle fracture without warning",
                    "Gradual reduction in Young's modulus",
                    "Chemical corrosion at the surface",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Distinguish between fatigue (progressive) and brittle fracture (sudden)",
                    "Clarify that fatigue affects strength, not necessarily modulus",
                    "Separate mechanical fatigue from chemical corrosion mechanisms",
                ],
            },
            {
                "topic": "Fracture Modes",
                "question": "What distinguishes ductile fracture from brittle fracture?",
                "options": [
                    "Ductile fracture involves significant plastic deformation before failure, while brittle fracture occurs with minimal deformation",
                    "Ductile fracture only occurs in metals, while brittle fracture only occurs in ceramics",
                    "Ductile fracture happens at high temperatures, brittle at low temperatures",
                    "There is no difference; they are the same phenomenon",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Explain that both metals and ceramics can exhibit either mode depending on conditions",
                    "Clarify that temperature affects but doesn't solely determine fracture mode",
                    "Emphasize the fundamental difference in deformation behavior",
                ],
            },
            {
                "topic": "Failure Criteria",
                "question": "When is the von Mises failure criterion most appropriate?",
                "options": [
                    "For ductile materials under multiaxial stress states",
                    "For brittle materials under uniaxial tension",
                    "For materials with anisotropic properties",
                    "For all materials regardless of ductility",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Explain why von Mises is not suitable for brittle materials",
                    "Clarify that von Mises assumes isotropic behavior",
                    "Distinguish between criteria for different material types",
                ],
            },
        ]

        for i, template in enumerate(templates[:num_tasks]):
            task_id = f"level_a_{i + 1}"
            task = LevelATask(
                id=task_id,
                topic=template["topic"],
                question=template["question"],
                options=template["options"],
                correct_option=template["correct_option"],
                rubric_explanation_points={
                    "technical_soundness": 5,
                    "conceptual_clarity": 5,
                    "distractor_analysis": 3,
                },
                distractor_analysis=template["distractor_analysis"],
            )

            self.db.add_task(
                task_id=task_id,
                level="A",
                topic=template["topic"],
                schema_type="LevelATask",
                schema_data=task.model_dump(),
            )

    def generate_level_b_tasks(self, num_tasks: int = 5):
        """Generate Level B tasks (parametric calculations)."""
        templates = [
            {
                "topic": "Euler-Bernoulli Beam Deflection",
                "problem_template": "A simply supported beam of length L = {L} m carries a point load P = {P} kN at its center. The beam has a rectangular cross-section with width b = {b} mm and height h = {h} mm. The material has Young's modulus E = {E} GPa. Calculate the maximum deflection at the center of the beam.",
                "symbolic_variables": {
                    "P": "Point load at center",
                    "L": "Beam length",
                    "E": "Young's modulus",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                },
                "units": {"P": "kN", "L": "m", "E": "GPa", "b": "mm", "h": "mm"},
                "ground_truth_formula": "P * 1000 * L**3 / (48 * E * 1e9 * b * h**3 / 12)",
                "parameter_ranges": {
                    "P": {"min": 1, "max": 100},
                    "L": {"min": 1, "max": 10},
                    "E": {"min": 200, "max": 210},
                    "b": {"min": 50, "max": 200},
                    "h": {"min": 100, "max": 500},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Axial Bar Extension",
                "problem_template": "A steel bar of length L = {L} m and cross-sectional area A = {A} mm² is subjected to an axial tensile force P = {P} kN. The material has Young's modulus E = {E} GPa. Calculate the elongation of the bar.",
                "symbolic_variables": {
                    "P": "Axial force",
                    "L": "Bar length",
                    "A": "Cross-sectional area",
                    "E": "Young's modulus",
                },
                "units": {"P": "kN", "L": "m", "A": "mm²", "E": "GPa"},
                "ground_truth_formula": "P * 1000 * L / (E * 1e9 * A * 1e-6)",
                "parameter_ranges": {
                    "P": {"min": 10, "max": 500},
                    "L": {"min": 0.5, "max": 5},
                    "A": {"min": 100, "max": 1000},
                    "E": {"min": 200, "max": 210},
                },
                "tolerance": 0.01,
            },
        ]

        for i, template in enumerate(templates[:num_tasks]):
            task_id = f"level_b_{i + 1}"

            # Sample parameters for reference solution
            params = {}
            for var, range_dict in template["parameter_ranges"].items():
                params[var] = random.uniform(range_dict["min"], range_dict["max"])

            # Calculate reference solution
            try:
                reference_solution = eval(
                    template["ground_truth_formula"], {"__builtins__": {}}, params
                )
            except:
                reference_solution = 0.0

            task = LevelBTask(
                id=task_id,
                topic=template["topic"],
                problem_template=template["problem_template"],
                symbolic_variables=template["symbolic_variables"],
                units=template["units"],
                ground_truth_formula=template["ground_truth_formula"],
                reference_solution=reference_solution,
                tolerance=template["tolerance"],
                parameter_ranges=template["parameter_ranges"],
            )

            self.db.add_task(
                task_id=task_id,
                level="B",
                topic=template["topic"],
                schema_type="LevelBTask",
                schema_data=task.model_dump(),
            )

    def generate_level_c_tasks(self, num_tasks: int = 5):
        """Generate Level C tasks (design & optimization)."""
        templates = [
            {
                "topic": "Cantilever Beam Frequency Optimization",
                "objectives": ["Maximize natural frequency", "Minimize mass"],
                "constraints": [
                    "Maximum deflection < 10 mm under static load",
                    "Stress < yield strength",
                    "Frequency > 50 Hz",
                ],
                "design_variables": {
                    "length": {
                        "type": "continuous",
                        "min": 0.5,
                        "max": 2.0,
                        "unit": "m",
                    },
                    "width": {
                        "type": "continuous",
                        "min": 0.05,
                        "max": 0.2,
                        "unit": "m",
                    },
                    "height": {
                        "type": "continuous",
                        "min": 0.1,
                        "max": 0.3,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum", "titanium"],
                    },
                },
                "reference_design": {
                    "length": 1.0,
                    "width": 0.1,
                    "height": 0.2,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum", "titanium"],
                "evaluation_criteria": {"frequency_weight": 0.6, "mass_weight": 0.4},
            }
        ]

        for i, template in enumerate(templates[:num_tasks]):
            task_id = f"level_c_{i + 1}"
            task = LevelCTask(
                id=task_id,
                topic=template["topic"],
                objectives=template["objectives"],
                constraints=template["constraints"],
                design_variables=template["design_variables"],
                reference_design=template["reference_design"],
                material_options=template["material_options"],
                evaluation_criteria=template["evaluation_criteria"],
            )

            self.db.add_task(
                task_id=task_id,
                level="C",
                topic=template["topic"],
                schema_type="LevelCTask",
                schema_data=task.model_dump(),
            )

    def generate_level_d_tasks(self, examples_dir: str | Path | None = None):
        """Generate Level D tasks by loading from JSON example files.

        Args:
            examples_dir: Directory containing Level D example JSON files.
                         Defaults to data/level_d/examples relative to project root.
        """
        if examples_dir is None:
            # Default to data/level_d/examples relative to project root
            project_root = Path(__file__).parent.parent.parent
            examples_dir = project_root / "data" / "level_d" / "examples"
        else:
            examples_dir = Path(examples_dir)

        if not examples_dir.exists():
            print(f"Warning: Level D examples directory not found: {examples_dir}")
            return []

        # Find all JSON files in examples directory
        json_files = list(examples_dir.glob("*.json"))

        loaded_tasks = []
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    task_data = json.load(f)

                # Validate it's a Level D task
                if task_data.get("level") != "D":
                    print(f"Warning: Skipping {json_file.name} - not a Level D task")
                    continue

                # Create LevelDTask schema object
                task = LevelDTask(**task_data)

                # Store in database
                self.db.add_task(
                    task_id=task_data["id"],
                    level="D",
                    topic=task_data.get("title", task_data.get("type", "")),
                    schema_type="LevelDTask",
                    schema_data=task.model_dump(),
                )

                loaded_tasks.append(task_data["id"])
                print(f"Loaded Level D task: {task_data['id']}")

            except Exception as e:
                print(f"Error loading Level D task from {json_file.name}: {e}")
                continue

        return loaded_tasks

    def generate_task_instances(self, task_id: str, num_instances: int = 10):
        """Generate multiple instances of a task with different parameters."""
        # Get task from database
        tasks_a = self.db.get_tasks_by_level("A")
        tasks_b = self.db.get_tasks_by_level("B")
        tasks_c = self.db.get_tasks_by_level("C")
        tasks_d = self.db.get_tasks_by_level("D")
        all_tasks = tasks_a + tasks_b + tasks_c + tasks_d

        task = next((t for t in all_tasks if t["id"] == task_id), None)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Parse schema_data (stored as JSON string in database)
        schema_data = (
            json.loads(task["schema_data"])
            if isinstance(task["schema_data"], str)
            else task["schema_data"]
        )
        level = task["level"]

        instances = []
        for i in range(num_instances):
            instance_id = f"{task_id}_instance_{i + 1}"

            if level == "A":
                # Level A instances are the same (no parameter variation)
                parameters = {}
                gold_answer = {
                    "correct_option": schema_data["correct_option"],
                    "explanation_required": True,
                }
            elif level == "B":
                # Sample parameters from ranges
                parameters = {}
                for var, range_dict in schema_data["parameter_ranges"].items():
                    parameters[var] = random.uniform(
                        range_dict["min"], range_dict["max"]
                    )

                # Calculate gold answer
                try:
                    solution = eval(
                        schema_data["ground_truth_formula"],
                        {"__builtins__": {}},
                        parameters,
                    )
                    gold_answer = {
                        "solution": solution,
                        "tolerance": schema_data["tolerance"],
                    }
                except:
                    gold_answer = {
                        "solution": 0.0,
                        "tolerance": schema_data["tolerance"],
                    }
            elif level == "C":
                # Level C: Sample design variables
                parameters = {}
                for var, var_info in schema_data["design_variables"].items():
                    if var_info["type"] == "continuous":
                        parameters[var] = random.uniform(
                            var_info["min"], var_info["max"]
                        )
                    else:
                        parameters[var] = random.choice(var_info["options"])

                gold_answer = {
                    "reference_design": schema_data["reference_design"],
                    "evaluation_required": True,
                }
            elif level == "D":
                # Level D: multi-step design task
                # For Level D, we can optionally vary parameters from the given values
                # For now, use empty parameters (Level D tasks are typically loaded from JSON with fixed parameters)
                parameters = {}
                gold_answer = {
                    "evaluation_required": True,
                    "multi_step": True,
                }
            else:
                raise ValueError(f"Unknown level: {level}")

            self.db.add_task_instance(
                instance_id=instance_id,
                task_id=task_id,
                parameters=parameters,
                gold_answer=gold_answer,
                metadata={"instance_number": i + 1},
            )
            instances.append(instance_id)

        return instances
