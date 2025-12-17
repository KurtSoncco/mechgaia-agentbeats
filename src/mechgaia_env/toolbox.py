"""Engineering toolbox with material database, math engine, and plotting."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import sympy as sp

from src.mechgaia_env.config import config

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None


class MaterialDatabase:
    """Material properties database."""

    def __init__(self, materials_file: Optional[Path] = None):
        self.materials_file = materials_file or config.materials_file
        self.materials = self._load_materials()

    def _load_materials(self) -> Dict[str, Dict[str, Any]]:
        """Load materials from JSON file."""
        if self.materials_file.exists():
            try:
                with open(self.materials_file, "r") as f:
                    return json.load(f)
            except Exception:
                return self._default_materials()
        else:
            return self._default_materials()

    def _default_materials(self) -> Dict[str, Dict[str, Any]]:
        """Default material properties."""
        return {
            "steel": {
                "name": "Steel (AISI 1020)",
                "youngs_modulus": 200e9,  # Pa
                "yield_strength": 350e6,  # Pa
                "ultimate_strength": 420e6,  # Pa
                "density": 7850,  # kg/m³
                "poissons_ratio": 0.3,
                "thermal_expansion": 12e-6,  # 1/K
                "class": "metal",
            },
            "aluminum": {
                "name": "Aluminum 6061",
                "youngs_modulus": 69e9,  # Pa
                "yield_strength": 276e6,  # Pa
                "ultimate_strength": 310e6,  # Pa
                "density": 2700,  # kg/m³
                "poissons_ratio": 0.33,
                "thermal_expansion": 23e-6,  # 1/K
                "class": "metal",
            },
            "titanium": {
                "name": "Titanium Grade 5",
                "youngs_modulus": 110e9,  # Pa
                "yield_strength": 880e6,  # Pa
                "ultimate_strength": 950e6,  # Pa
                "density": 4500,  # kg/m³
                "poissons_ratio": 0.34,
                "thermal_expansion": 8.6e-6,  # 1/K
                "class": "metal",
            },
            "composite": {
                "name": "Carbon Fiber Composite",
                "youngs_modulus": 70e9,  # Pa (typical)
                "yield_strength": 600e6,  # Pa
                "ultimate_strength": 800e6,  # Pa
                "density": 1600,  # kg/m³
                "poissons_ratio": 0.3,
                "thermal_expansion": 2e-6,  # 1/K
                "class": "composite",
            },
        }

    def get_material_properties(self, material_name: str) -> Optional[Dict[str, Any]]:
        """Get properties for a material.

        Args:
            material_name: Name of material (case-insensitive)

        Returns:
            Dictionary of material properties or None if not found
        """
        material_name_lower = material_name.lower()
        return self.materials.get(material_name_lower)

    def list_materials(self) -> List[str]:
        """List all available materials."""
        return list(self.materials.keys())


class MathEngine:
    """Mathematical computation engine using NumPy and SymPy."""

    def __init__(self):
        pass

    def evaluate_formula(self, formula: str, variables: Dict[str, float]) -> float:
        """Evaluate a mathematical formula.

        Args:
            formula: Formula string (Python-compatible)
            variables: Dictionary of variable values

        Returns:
            Computed result
        """
        safe_dict = {
            "__builtins__": {},
            "np": np,
            "numpy": np,
            "sqrt": np.sqrt,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "exp": np.exp,
            "log": np.log,
            "pi": np.pi,
            "e": np.e,
            **variables,
        }

        return eval(formula, safe_dict)

    def symbolic_solve(self, equation: str, variable: str) -> Any:
        """Solve equation symbolically.

        Args:
            equation: Equation string
            variable: Variable to solve for

        Returns:
            SymPy solution
        """
        x = sp.Symbol(variable)
        eq = sp.sympify(equation)
        return sp.solve(eq, x)


class PlottingBackend:
    """Plotting backend for engineering diagrams."""

    def __init__(self):
        pass

    def plot_stress_strain(
        self,
        stress: List[float],
        strain: List[float],
        yield_point: Optional[float] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Plot stress-strain curve.

        Args:
            stress: List of stress values
            strain: List of strain values
            yield_point: Yield strength (optional)
            output_path: Path to save plot

        Returns:
            Dictionary with validation results
        """
        if not MATPLOTLIB_AVAILABLE:
            return {"error": "matplotlib not available"}

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(strain, stress, "b-", linewidth=2)

        if yield_point:
            ax.axhline(
                y=yield_point,
                color="r",
                linestyle="--",
                label=f"Yield Strength: {yield_point / 1e6:.1f} MPa",
            )

        ax.set_xlabel("Strain", fontsize=12)
        ax.set_ylabel("Stress (Pa)", fontsize=12)
        ax.set_title("Stress-Strain Curve", fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")

        plt.close()

        # Validation
        validation = {
            "has_labels": True,
            "has_yield_point": yield_point is not None,
            "data_points": len(stress),
        }

        return validation

    def plot_bending_moment(
        self,
        positions: List[float],
        moments: List[float],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Plot bending moment diagram.

        Args:
            positions: List of positions along beam
            moments: List of moment values
            output_path: Path to save plot

        Returns:
            Dictionary with validation results
        """
        if not MATPLOTLIB_AVAILABLE:
            return {"error": "matplotlib not available"}

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(positions, moments, "g-", linewidth=2)
        ax.fill_between(positions, moments, alpha=0.3)
        ax.axhline(y=0, color="k", linestyle="-", linewidth=0.5)

        ax.set_xlabel("Position (m)", fontsize=12)
        ax.set_ylabel("Bending Moment (N⋅m)", fontsize=12)
        ax.set_title("Bending Moment Diagram", fontsize=14)
        ax.grid(True, alpha=0.3)

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")

        plt.close()

        # Validation
        validation = {
            "has_labels": True,
            "has_zero_line": True,
            "data_points": len(moments),
        }

        return validation

    def validate_diagram(
        self, diagram_type: str, data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate engineering diagram.

        Args:
            diagram_type: Type of diagram ('stress_strain', 'bending_moment', etc.)
            data: Diagram data

        Returns:
            Dictionary with validation results
        """
        validation = {}

        if diagram_type == "stress_strain":
            validation["has_stress"] = "stress" in data
            validation["has_strain"] = "strain" in data
            validation["lengths_match"] = len(data.get("stress", [])) == len(
                data.get("strain", [])
            )
            validation["positive_stress"] = all(s >= 0 for s in data.get("stress", []))

        elif diagram_type == "bending_moment":
            validation["has_positions"] = "positions" in data
            validation["has_moments"] = "moments" in data
            validation["lengths_match"] = len(data.get("positions", [])) == len(
                data.get("moments", [])
            )

        return validation


class EngineeringToolbox:
    """Main engineering toolbox combining all tools."""

    def __init__(self):
        self.materials = MaterialDatabase()
        self.math = MathEngine()
        self.plotting = PlottingBackend()

    def get_material_properties(self, material_name: str) -> Optional[Dict[str, Any]]:
        """Get material properties."""
        return self.materials.get_material_properties(material_name)

    def evaluate_formula(self, formula: str, variables: Dict[str, float]) -> float:
        """Evaluate mathematical formula."""
        return self.math.evaluate_formula(formula, variables)

    def plot_stress_strain(
        self,
        stress: List[float],
        strain: List[float],
        yield_point: Optional[float] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Plot stress-strain curve."""
        return self.plotting.plot_stress_strain(
            stress, strain, yield_point, output_path
        )

    def validate_diagram(
        self, diagram_type: str, data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate engineering diagram."""
        return self.plotting.validate_diagram(diagram_type, data)
