"""Prime Memory Folding.

A standalone prime-addressed memory system with vector-aware folding.
"""

from .address import PrimeAddress, stable_instance_id
from .folding import FoldResult, FoldingPolicy, MemoryFolder
from .sqlite_store import (
    export_sqlite_to_json,
    load_store_from_sqlite,
    migrate_json_to_sqlite,
    save_store_to_sqlite,
)
from .store import MemoryRecord, PrimeMemoryStore
from .system import PrimeMemorySystem, backend_for_path
from .vectors import cosine_similarity

__all__ = [
    "FoldResult",
    "FoldingPolicy",
    "MemoryFolder",
    "MemoryRecord",
    "PrimeAddress",
    "PrimeMemoryStore",
    "PrimeMemorySystem",
    "backend_for_path",
    "cosine_similarity",
    "export_sqlite_to_json",
    "load_store_from_sqlite",
    "migrate_json_to_sqlite",
    "save_store_to_sqlite",
    "stable_instance_id",
]

__version__ = "0.1.0"
