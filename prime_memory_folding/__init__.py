"""Prime Memory Folding.

A standalone prime-addressed memory system with vector-aware folding.
"""

from .address import PrimeAddress, stable_instance_id
from .folding import FoldResult, FoldingPolicy, MemoryFolder
from .store import MemoryRecord, PrimeMemoryStore
from .system import PrimeMemorySystem
from .vectors import cosine_similarity

__all__ = [
    "FoldResult",
    "FoldingPolicy",
    "MemoryFolder",
    "MemoryRecord",
    "PrimeAddress",
    "PrimeMemoryStore",
    "PrimeMemorySystem",
    "cosine_similarity",
    "stable_instance_id",
]

__version__ = "0.1.0"
