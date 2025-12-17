"""Configuration for MechGAIA benchmark system."""

from pathlib import Path

from pydantic_settings import BaseSettings


class BenchmarkConfig(BaseSettings):
    """Configuration for the benchmark system."""

    # Database configuration
    database_path: str = "data/benchmark.db"

    # LLM Judge configuration
    llm_judge_model: str = "openai/gpt-4o"
    llm_judge_provider: str = "openai"

    # Contamination detection
    contamination_threshold: float = 0.3
    ngram_sizes: list[int] = [3, 5]

    # Bootstrap configuration
    bootstrap_iterations: int = 1000
    confidence_level: float = 0.95

    # Sandbox configuration
    sandbox_timeout: int = 30  # seconds

    # A2A client configuration
    a2a_timeout: float = 600.0  # seconds (10 minutes for long-running agent operations)
    a2a_connect_timeout: float = 30.0  # seconds

    # Data directories
    data_dir: Path = Path("data")
    materials_file: Path = Path("data/materials.json")
    corpus_dir: Path = Path("data/textbook_corpus")

    class Config:
        env_prefix = "MECHGAIA_"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = BenchmarkConfig()
