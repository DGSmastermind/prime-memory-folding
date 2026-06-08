"""Small vector utilities with no mandatory third-party dependencies."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence


def as_float_vector(values: Iterable[float] | None) -> List[float]:
    if values is None:
        return []
    return [float(value) for value in values]


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    size = min(len(left), len(right))
    return sum(left[i] * right[i] for i in range(size))


def norm(values: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity in the range [-1, 1]."""
    if not left or not right:
        return 0.0
    left_norm = norm(left)
    right_norm = norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot(left, right) / (left_norm * right_norm)))


def weighted_average(vectors: Sequence[Sequence[float]], weights: Sequence[float]) -> List[float]:
    """Return a dimension-wise weighted average."""
    if not vectors:
        return []
    width = max(len(vector) for vector in vectors)
    total_weight = sum(weights)
    if total_weight <= 0:
        total_weight = float(len(vectors))
        weights = [1.0 for _ in vectors]

    output = [0.0 for _ in range(width)]
    for vector, weight in zip(vectors, weights):
        for index, value in enumerate(vector):
            output[index] += value * weight
    return [value / total_weight for value in output]


def clamp_vector(values: Sequence[float], minimum: float = -1.0, maximum: float = 1.0) -> List[float]:
    return [max(minimum, min(maximum, float(value))) for value in values]
