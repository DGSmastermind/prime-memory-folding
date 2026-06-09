"""High-level Prime Memory Folding facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .folding import FoldResult, MemoryFolder
from .sqlite_store import load_store_from_sqlite, save_store_to_sqlite
from .store import MemoryRecord, PrimeMemoryStore

_SQLITE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
_VALID_BACKENDS = ("json", "sqlite")


def backend_for_path(path: Optional[Path]) -> str:
    """Infer the persistence backend from a store path's suffix."""
    if path is not None and str(path).lower().endswith(_SQLITE_SUFFIXES):
        return "sqlite"
    return "json"


class PrimeMemorySystem:
    """Convenience facade combining store, retrieval, folding, and persistence.

    Persistence backend is JSON by default, or SQLite when the store path ends
    in ``.db``/``.sqlite``/``.sqlite3`` (or when ``backend="sqlite"`` is passed).
    """

    def __init__(self, path: str | Path | None = None, backend: Optional[str] = None) -> None:
        self.path = Path(path) if path else None
        resolved = (backend or backend_for_path(self.path)).lower()
        if resolved not in _VALID_BACKENDS:
            raise ValueError(
                f"unknown backend {resolved!r}; expected one of {sorted(_VALID_BACKENDS)}"
            )
        self.backend = resolved
        if self.path is None:
            self.store = PrimeMemoryStore()
        elif self.backend == "sqlite":
            self.store = load_store_from_sqlite(self.path)
        else:
            self.store = PrimeMemoryStore.load(self.path)
        self.folder = MemoryFolder()

    def remember(
        self,
        content: str,
        domain: str = "memory",
        subdomain: str = "general",
        tags: Optional[Iterable[str]] = None,
        vector: Optional[Iterable[float]] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        record = self.store.add(
            content=content,
            domain=domain,
            subdomain=subdomain,
            tags=tags,
            vector=vector,
            importance=importance,
            metadata=metadata,
        )
        self.save()
        return record

    def recall(
        self,
        domain: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        vector: Optional[Iterable[float]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if vector is not None:
            return [
                {"record": item["record"].to_dict(), "similarity": item["similarity"]}
                for item in self.store.similar(vector, domain=domain, tags=tags, limit=limit)
            ]
        return [{"record": record.to_dict()} for record in self.store.query(domain, tags, limit=limit)]

    def fold(self) -> FoldResult:
        result = self.folder.fold_store(self.store)
        self.save()
        return result

    def encode(
        self,
        domain: str,
        subdomain: str = "general",
        tags: Optional[Iterable[str]] = None,
        instance_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        address = self.store.encode(domain, subdomain, tags, instance_key)
        return {
            "address": address.pack(),
            "address_hex": address.to_hex(),
            "domain": address.domain,
            "subdomain": address.subdomain,
            "concept": address.concept,
            "instance": address.instance,
        }

    def stats(self) -> Dict[str, Any]:
        return self.store.stats()

    def save(self) -> None:
        if not self.path:
            return
        if self.backend == "sqlite":
            save_store_to_sqlite(self.store, self.path)
        else:
            self.store.save(self.path)
