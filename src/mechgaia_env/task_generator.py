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
            {
                "topic": "Stress-Strain Curve Interpretation",
                "question": "On a typical stress-strain curve for a ductile metal, what does the area under the curve up to the ultimate tensile strength represent?",
                "options": [
                    "The toughness or energy absorbed per unit volume before necking begins",
                    "The elastic modulus of the material",
                    "The yield strength multiplied by the strain",
                    "The total elongation of the specimen",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Clarify that elastic modulus is the slope of the linear region, not the area",
                    "Explain that yield strength times strain is only part of the area",
                    "Distinguish between energy absorption (area) and geometric deformation (elongation)",
                ],
            },
            {
                "topic": "Creep vs Relaxation",
                "question": "What is the key difference between creep and stress relaxation?",
                "options": [
                    "Creep occurs under constant stress with increasing strain, while relaxation occurs under constant strain with decreasing stress",
                    "Creep only happens at high temperatures, while relaxation occurs at room temperature",
                    "Creep applies to metals, while relaxation applies to polymers",
                    "They are the same phenomenon with different names",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Clarify that both creep and relaxation are temperature-dependent but can occur at various temperatures",
                    "Explain that both metals and polymers can exhibit creep and relaxation",
                    "Emphasize the fundamental difference: constant stress vs constant strain conditions",
                ],
            },
            {
                "topic": "Composite Material Anisotropy",
                "question": "Why are fiber-reinforced composite materials typically anisotropic?",
                "options": [
                    "The mechanical properties differ along different directions due to the oriented fiber reinforcement",
                    "Composite materials are always isotropic regardless of fiber orientation",
                    "Anisotropy only occurs in metal matrix composites, not polymer matrix composites",
                    "The matrix material determines anisotropy, not the fibers",
                ],
                "correct_option": 0,
                "distractor_analysis": [
                    "Clarify that fiber orientation creates anisotropy in both metal and polymer matrix composites",
                    "Explain that while the matrix contributes, fiber orientation is the primary source of anisotropy",
                    "Distinguish between isotropic matrix materials and anisotropic composite behavior",
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
            {
                "topic": "Cantilever Beam Tip Deflection",
                "problem_template": "A cantilever beam of length L = {L} m carries a point load P = {P} kN at its free end. The beam has a rectangular cross-section with width b = {b} mm and height h = {h} mm. The material has Young's modulus E = {E} GPa. Calculate the tip deflection.",
                "symbolic_variables": {
                    "P": "Point load at tip",
                    "L": "Beam length",
                    "E": "Young's modulus",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                },
                "units": {"P": "kN", "L": "m", "E": "GPa", "b": "mm", "h": "mm"},
                "ground_truth_formula": "P * 1000 * L**3 / (3 * E * 1e9 * b * h**3 / 12)",
                "parameter_ranges": {
                    "P": {"min": 1, "max": 50},
                    "L": {"min": 0.5, "max": 5},
                    "E": {"min": 200, "max": 210},
                    "b": {"min": 50, "max": 200},
                    "h": {"min": 100, "max": 400},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Torsional Shaft Angle of Twist",
                "problem_template": "A circular shaft of length L = {L} m and diameter d = {d} mm is subjected to a torque T = {T} N⋅m. The material has shear modulus G = {G} GPa. Calculate the angle of twist in radians.",
                "symbolic_variables": {
                    "T": "Applied torque",
                    "L": "Shaft length",
                    "d": "Shaft diameter",
                    "G": "Shear modulus",
                },
                "units": {"T": "N⋅m", "L": "m", "d": "mm", "G": "GPa"},
                "ground_truth_formula": "T * L / (G * 1e9 * 3.14159 * (d * 1e-3 / 2)**4 / 2)",
                "parameter_ranges": {
                    "T": {"min": 100, "max": 10000},
                    "L": {"min": 0.5, "max": 3},
                    "d": {"min": 20, "max": 100},
                    "G": {"min": 75, "max": 80},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Thin-Walled Pressure Vessel Hoop Stress",
                "problem_template": "A thin-walled cylindrical pressure vessel has an internal radius r = {r} mm and wall thickness t = {t} mm. The vessel is subjected to an internal pressure p = {p} MPa. Calculate the hoop stress.",
                "symbolic_variables": {
                    "p": "Internal pressure",
                    "r": "Internal radius",
                    "t": "Wall thickness",
                },
                "units": {"p": "MPa", "r": "mm", "t": "mm"},
                "ground_truth_formula": "p * 1e6 * r * 1e-3 / (t * 1e-3)",
                "parameter_ranges": {
                    "p": {"min": 0.5, "max": 10},
                    "r": {"min": 50, "max": 500},
                    "t": {"min": 2, "max": 20},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Column Buckling Critical Load",
                "problem_template": "A column of length L = {L} m with a rectangular cross-section (width b = {b} mm, height h = {h} mm) is pinned at both ends. The material has Young's modulus E = {E} GPa. Calculate the Euler buckling critical load.",
                "symbolic_variables": {
                    "L": "Column length",
                    "E": "Young's modulus",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                },
                "units": {"L": "m", "E": "GPa", "b": "mm", "h": "mm"},
                "ground_truth_formula": "3.14159**2 * E * 1e9 * b * h**3 / (12 * L**2)",
                "parameter_ranges": {
                    "L": {"min": 1, "max": 5},
                    "E": {"min": 200, "max": 210},
                    "b": {"min": 50, "max": 200},
                    "h": {"min": 100, "max": 300},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Bending Stress in Beam",
                "problem_template": "A simply supported beam of length L = {L} m carries a uniform distributed load w = {w} kN/m. The beam has a rectangular cross-section with width b = {b} mm and height h = {h} mm. Calculate the maximum bending stress at midspan.",
                "symbolic_variables": {
                    "w": "Distributed load",
                    "L": "Beam length",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                },
                "units": {"w": "kN/m", "L": "m", "b": "mm", "h": "mm"},
                "ground_truth_formula": "w * 1000 * L**2 / 8 * (h * 1e-3 / 2) / (b * h**3 / 12)",
                "parameter_ranges": {
                    "w": {"min": 1, "max": 50},
                    "L": {"min": 2, "max": 8},
                    "b": {"min": 50, "max": 200},
                    "h": {"min": 150, "max": 400},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Combined Axial and Bending Stress",
                "problem_template": "A column of length L = {L} m with rectangular cross-section (width b = {b} mm, height h = {h} mm) is subjected to an axial compressive force P = {P} kN and a bending moment M = {M} kN⋅m. The material has Young's modulus E = {E} GPa. Calculate the maximum combined stress (compressive).",
                "symbolic_variables": {
                    "P": "Axial compressive force",
                    "M": "Bending moment",
                    "L": "Column length",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                    "E": "Young's modulus",
                },
                "units": {
                    "P": "kN",
                    "M": "kN⋅m",
                    "L": "m",
                    "b": "mm",
                    "h": "mm",
                    "E": "GPa",
                },
                "ground_truth_formula": "P * 1000 / (b * h * 1e-6) + M * 1000 * (h * 1e-3 / 2) / (b * h**3 / 12)",
                "parameter_ranges": {
                    "P": {"min": 50, "max": 500},
                    "M": {"min": 5, "max": 50},
                    "L": {"min": 2, "max": 6},
                    "b": {"min": 100, "max": 300},
                    "h": {"min": 150, "max": 400},
                    "E": {"min": 200, "max": 210},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Thin Plate Bending Deflection",
                "problem_template": "A simply supported rectangular plate with dimensions a = {a} m (length) and b = {b} m (width) is subjected to a uniform pressure p = {p} kPa. The plate has thickness t = {t} mm and material properties E = {E} GPa and Poisson's ratio nu = {nu}. Calculate the maximum deflection at the center of the plate.",
                "symbolic_variables": {
                    "p": "Uniform pressure",
                    "a": "Plate length",
                    "b": "Plate width",
                    "t": "Plate thickness",
                    "E": "Young's modulus",
                    "nu": "Poisson's ratio",
                },
                "units": {
                    "p": "kPa",
                    "a": "m",
                    "b": "m",
                    "t": "mm",
                    "E": "GPa",
                    "nu": "dimensionless",
                },
                "ground_truth_formula": "p * 1000 * a**4 * (5 - nu) / (384 * E * 1e9 * (t * 1e-3)**3 / (12 * (1 - nu**2)))",
                "parameter_ranges": {
                    "p": {"min": 1, "max": 20},
                    "a": {"min": 0.5, "max": 2.0},
                    "b": {"min": 0.5, "max": 2.0},
                    "t": {"min": 5, "max": 25},
                    "E": {"min": 200, "max": 210},
                    "nu": {"min": 0.25, "max": 0.30},
                },
                "tolerance": 0.01,
            },
            {
                "topic": "Energy Methods (Castigliano) for Deflection",
                "problem_template": "A cantilever beam of length L = {L} m carries a point load P = {P} kN at its free end. The beam has a rectangular cross-section with width b = {b} mm and height h = {h} mm. The material has Young's modulus E = {E} GPa. Using Castigliano's theorem, calculate the tip deflection.",
                "symbolic_variables": {
                    "P": "Point load at tip",
                    "L": "Beam length",
                    "b": "Cross-section width",
                    "h": "Cross-section height",
                    "E": "Young's modulus",
                },
                "units": {"P": "kN", "L": "m", "b": "mm", "h": "mm", "E": "GPa"},
                "ground_truth_formula": "P * 1000 * L**3 / (3 * E * 1e9 * b * h**3 / 12)",
                "parameter_ranges": {
                    "P": {"min": 1, "max": 50},
                    "L": {"min": 0.5, "max": 5},
                    "b": {"min": 50, "max": 200},
                    "h": {"min": 100, "max": 400},
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
            },
            {
                "topic": "Simply Supported Beam Mass Minimization",
                "objectives": ["Minimize mass", "Maximize stiffness"],
                "constraints": [
                    "Maximum deflection < 5 mm under distributed load",
                    "Maximum stress < 200 MPa",
                    "Beam length fixed at 3.0 m",
                ],
                "design_variables": {
                    "width": {
                        "type": "continuous",
                        "min": 0.08,
                        "max": 0.25,
                        "unit": "m",
                    },
                    "height": {
                        "type": "continuous",
                        "min": 0.15,
                        "max": 0.40,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "width": 0.15,
                    "height": 0.25,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"mass_weight": 0.7, "stiffness_weight": 0.3},
            },
            {
                "topic": "Column Design for Maximum Load Capacity",
                "objectives": [
                    "Maximize buckling load",
                    "Minimize cross-sectional area",
                ],
                "constraints": [
                    "Column length fixed at 4.0 m",
                    "Slenderness ratio < 200",
                    "Material yield strength > 250 MPa",
                ],
                "design_variables": {
                    "width": {
                        "type": "continuous",
                        "min": 0.10,
                        "max": 0.30,
                        "unit": "m",
                    },
                    "height": {
                        "type": "continuous",
                        "min": 0.10,
                        "max": 0.30,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "width": 0.15,
                    "height": 0.20,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"load_weight": 0.6, "area_weight": 0.4},
            },
            {
                "topic": "Pressure Vessel Wall Thickness Optimization",
                "objectives": ["Minimize wall thickness", "Maximize safety factor"],
                "constraints": [
                    "Internal pressure = 5 MPa",
                    "Vessel radius = 0.5 m",
                    "Safety factor >= 2.0",
                    "Hoop stress < yield strength",
                ],
                "design_variables": {
                    "thickness": {
                        "type": "continuous",
                        "min": 0.005,
                        "max": 0.050,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "thickness": 0.015,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"thickness_weight": 0.5, "safety_weight": 0.5},
            },
            {
                "topic": "Shaft Design for Torsional Strength",
                "objectives": ["Maximize torque capacity", "Minimize diameter"],
                "constraints": [
                    "Shaft length = 2.0 m",
                    "Maximum shear stress < 100 MPa",
                    "Angle of twist < 0.1 rad",
                ],
                "design_variables": {
                    "diameter": {
                        "type": "continuous",
                        "min": 0.05,
                        "max": 0.20,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "diameter": 0.10,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"torque_weight": 0.6, "diameter_weight": 0.4},
            },
            {
                "topic": "Truss Member Sizing Under Combined Load Cases",
                "objectives": [
                    "Minimize total member cross-sectional area",
                    "Satisfy stress constraints under multiple load combinations",
                ],
                "constraints": [
                    "Maximum tensile stress < 200 MPa",
                    "Maximum compressive stress < 150 MPa",
                    "Member buckling factor > 2.0",
                    "Truss geometry fixed (span = 6 m, height = 3 m)",
                ],
                "design_variables": {
                    "top_chord_area": {
                        "type": "continuous",
                        "min": 500,
                        "max": 2000,
                        "unit": "mm²",
                    },
                    "bottom_chord_area": {
                        "type": "continuous",
                        "min": 500,
                        "max": 2000,
                        "unit": "mm²",
                    },
                    "diagonal_area": {
                        "type": "continuous",
                        "min": 300,
                        "max": 1500,
                        "unit": "mm²",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "top_chord_area": 1200,
                    "bottom_chord_area": 1000,
                    "diagonal_area": 600,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"area_weight": 0.7, "safety_weight": 0.3},
            },
            {
                "topic": "Plate Thickness Optimization Under Pressure",
                "objectives": [
                    "Minimize plate thickness",
                    "Maximize safety factor against yielding",
                ],
                "constraints": [
                    "Internal pressure = 3 MPa",
                    "Plate radius = 0.8 m",
                    "Maximum deflection < 5 mm",
                    "Safety factor >= 2.5",
                ],
                "design_variables": {
                    "thickness": {
                        "type": "continuous",
                        "min": 0.008,
                        "max": 0.040,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "aluminum"],
                    },
                },
                "reference_design": {
                    "thickness": 0.015,
                    "material": "steel",
                },
                "material_options": ["steel", "aluminum"],
                "evaluation_criteria": {"thickness_weight": 0.6, "safety_weight": 0.4},
            },
            {
                "topic": "Multi-Column Layout Optimization for Slab",
                "objectives": [
                    "Minimize number of columns",
                    "Minimize total column cross-sectional area",
                ],
                "constraints": [
                    "Slab span between columns < 5 m",
                    "Column buckling load > applied load",
                    "Maximum column stress < 150 MPa",
                    "Slab area = 200 m²",
                ],
                "design_variables": {
                    "column_spacing": {
                        "type": "continuous",
                        "min": 3.0,
                        "max": 5.0,
                        "unit": "m",
                    },
                    "column_diameter": {
                        "type": "continuous",
                        "min": 0.20,
                        "max": 0.40,
                        "unit": "m",
                    },
                    "material": {
                        "type": "categorical",
                        "options": ["steel", "concrete"],
                    },
                },
                "reference_design": {
                    "column_spacing": 4.5,
                    "column_diameter": 0.30,
                    "material": "steel",
                },
                "material_options": ["steel", "concrete"],
                "evaluation_criteria": {"spacing_weight": 0.5, "area_weight": 0.5},
            },
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
