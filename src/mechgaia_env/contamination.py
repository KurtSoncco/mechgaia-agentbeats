"""Contamination detection using n-gram overlap."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.mechgaia_env.config import config


class ContaminationDetector:
    """Detects contamination using n-gram overlap with reference corpus."""

    def __init__(self, corpus_path: Optional[Path] = None):
        self.corpus_path = corpus_path or config.corpus_dir / "ngrams.json"
        self.ngram_sizes = config.ngram_sizes
        self.threshold = config.contamination_threshold
        self.corpus_ngrams: Dict[int, Set[str]] = {}
        self._load_corpus()

    def _load_corpus(self):
        """Load n-gram corpus from file."""
        if self.corpus_path.exists():
            try:
                with open(self.corpus_path, "r") as f:
                    data = json.load(f)
                    self.corpus_ngrams = {int(k): set(v) for k, v in data.items()}
            except Exception:
                self.corpus_ngrams = {}
        else:
            self.corpus_ngrams = {}

    def _extract_ngrams(self, text: str, n: int) -> Set[str]:
        """Extract n-grams from text.

        Args:
            text: Input text
            n: N-gram size

        Returns:
            Set of n-grams
        """
        words = text.lower().split()
        if len(words) < n:
            return set()

        ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i : i + n])
            ngrams.add(ngram)

        return ngrams

    def _text_to_ngrams(self, text: str) -> Dict[int, Set[str]]:
        """Extract n-grams of multiple sizes from text.

        Args:
            text: Input text

        Returns:
            Dictionary mapping n-gram size to set of n-grams
        """
        result = {}
        for n in self.ngram_sizes:
            result[n] = self._extract_ngrams(text, n)
        return result

    def compute_overlap(self, text: str, n: Optional[int] = None) -> float:
        """Compute n-gram overlap with corpus.

        Args:
            text: Text to check
            n: Specific n-gram size, or None for weighted average

        Returns:
            Overlap score (0-1)
        """
        text_ngrams = self._text_to_ngrams(text)

        if n:
            # Single n-gram size
            if n not in self.corpus_ngrams or not self.corpus_ngrams[n]:
                return 0.0

            text_set = text_ngrams.get(n, set())
            corpus_set = self.corpus_ngrams[n]

            if not text_set:
                return 0.0

            overlap = len(text_set & corpus_set)
            return overlap / len(text_set)
        else:
            # Weighted average across n-gram sizes
            overlaps = []
            for n_size in self.ngram_sizes:
                if n_size not in self.corpus_ngrams or not self.corpus_ngrams[n_size]:
                    continue

                text_set = text_ngrams.get(n_size, set())
                corpus_set = self.corpus_ngrams[n_size]

                if not text_set:
                    continue

                overlap = len(text_set & corpus_set) / len(text_set)
                overlaps.append(overlap)

            return sum(overlaps) / len(overlaps) if overlaps else 0.0

    def is_contaminated(self, text: str) -> bool:
        """Check if text is contaminated.

        Args:
            text: Text to check

        Returns:
            True if contamination detected
        """
        overlap = self.compute_overlap(text)
        return overlap >= self.threshold

    def check_task(self, task_text: str) -> Dict[str, Any]:
        """Check a task for contamination.

        Args:
            task_text: Task text to check

        Returns:
            Dictionary with contamination analysis
        """
        overlap = self.compute_overlap(task_text)
        is_contaminated = overlap >= self.threshold

        # Per n-gram size breakdown
        breakdown = {}
        for n in self.ngram_sizes:
            breakdown[f"{n}-gram"] = self.compute_overlap(task_text, n=n)

        return {
            "is_contaminated": is_contaminated,
            "overlap_score": overlap,
            "threshold": self.threshold,
            "breakdown": breakdown,
        }


def build_ngram_corpus(
    texts: List[str], output_path: Path, ngram_sizes: List[int] = [3, 5]
):
    """Build n-gram corpus from texts.

    Args:
        texts: List of text strings
        output_path: Path to save corpus
        ngram_sizes: List of n-gram sizes to extract
    """
    corpus_ngrams = {}

    for n in ngram_sizes:
        all_ngrams = set()
        for text in texts:
            words = text.lower().split()
            for i in range(len(words) - n + 1):
                ngram = tuple(words[i : i + n])
                all_ngrams.add(ngram)
        corpus_ngrams[n] = list(all_ngrams)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(corpus_ngrams, f, indent=2)
