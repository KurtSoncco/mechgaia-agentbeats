"""Type definitions for MechGAIA environment."""

from dataclasses import dataclass
from typing import Any, Dict

RESPOND_ACTION_NAME = "respond"


@dataclass
class Action:
    """Action that can be taken in the environment."""

    name: str
    kwargs: Dict[str, Any]


@dataclass
class SolveResult:
    """Result of solving a task."""

    reward: float
    info: Dict[str, Any]
    messages: list
    total_cost: float
