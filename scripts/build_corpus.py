#!/usr/bin/env python3
"""CLI script to build n-gram corpus from textbook examples."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer

from src.mechgaia_env.config import config
from src.mechgaia_env.contamination import build_ngram_corpus

app = typer.Typer()


@app.command()
def build(
    input_dir: str = typer.Option(
        None, "--input", "-i", help="Input directory with text files"
    ),
    output_path: str = typer.Option(
        None, "--output", "-o", help="Output path for corpus JSON"
    ),
    ngram_sizes: str = typer.Option(
        "3,5", "--ngram-sizes", help="Comma-separated n-gram sizes"
    ),
):
    """Build n-gram corpus from text files."""
    input_dir_path = Path(input_dir) if input_dir else config.corpus_dir
    output_path_obj = (
        Path(output_path) if output_path else config.corpus_dir / "ngrams.json"
    )

    ngram_size_list = [int(n) for n in ngram_sizes.split(",")]

    typer.echo(f"Building corpus from {input_dir_path}...")

    # Collect all text files
    texts = []
    if input_dir_path.exists():
        for text_file in input_dir_path.glob("*.txt"):
            with open(text_file, "r") as f:
                texts.append(f.read())
            typer.echo(f"  ✓ Loaded {text_file.name}")
    else:
        typer.echo(
            f"Input directory {input_dir_path} does not exist. Creating empty corpus.",
            err=True,
        )
        texts = []

    if not texts:
        typer.echo("Warning: No text files found. Creating empty corpus.")

    # Build corpus
    build_ngram_corpus(texts, output_path_obj, ngram_sizes=ngram_size_list)

    typer.echo(f"✓ Built corpus with {len(texts)} texts")
    typer.echo(f"✓ Saved to {output_path_obj}")


if __name__ == "__main__":
    app()
