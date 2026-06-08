"""Prime-addressed memory store."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .address import PrimeAddress, stable_instance_id
from .primes import (
    DEFAULT_DOMAIN_PRIMES,
    DEFAULT_SUBDOMAIN_PRIMES,
    DEFAULT_TAG_PRIMES,
    PrimeRegistry,
)
from .vectors import as_float_vector, cosine_similarity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class MemoryRecord:
    """A single memory item in the standalone store."""

    record_id: str
    address: int
    domain: str
    subdomain: str
    content: str
    tags: List[str] = field(default_factory=list)
    tag_product: int = 1
    vector: List[float] = field(default_factory=list)
    importance: float = 0.5
    strength: float = 1.0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def score(self) -> float:
        return max(0.0, min(1.0, self.importance)) * max(0.0, min(1.0, self.strength))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "address": self.address,
            "address_hex": PrimeAddress.unpack(self.address).to_hex(),
            "domain": self.domain,
            "subdomain": self.subdomain,
            "content": self.content,
            "tags": self.tags,
            "tag_product": self.tag_product,
            "vector": self.vector,
            "importance": self.importance,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryRecord":
        return cls(
            record_id=data["record_id"],
            address=int(data["address"]),
            domain=data["domain"],
            subdomain=data.get("subdomain", "general"),
            content=data["content"],
            tags=list(data.get("tags", [])),
            tag_product=int(data.get("tag_product", 1)),
            vector=as_float_vector(data.get("vector")),
            importance=float(data.get("importance", 0.5)),
            strength=float(data.get("strength", 1.0)),
            created_at=parse_dt(data["created_at"]),
            updated_at=parse_dt(data["updated_at"]),
            metadata=dict(data.get("metadata", {})),
        )

    def has_all_tag_primes(self, tag_product: int) -> bool:
        # Operate directly on the unbounded tag product. Avoids a per-record
        # PrimeAddress.unpack() (dataclass construction + range checks) that
        # dominated query cost; the concept lane is not used for tag filtering.
        if tag_product <= 1:
            return True
        return self.tag_product % tag_product == 0


class PrimeMemoryStore:
    """In-memory prime-addressed store with JSON persistence."""

    def __init__(
        self,
        domain_primes: Optional[Dict[str, int]] = None,
        subdomain_primes: Optional[Dict[str, int]] = None,
        tag_primes: Optional[Dict[str, int]] = None,
    ) -> None:
        self.domain_registry = PrimeRegistry.with_defaults(domain_primes or DEFAULT_DOMAIN_PRIMES)
        self.subdomain_registry = PrimeRegistry.with_defaults(
            subdomain_primes or DEFAULT_SUBDOMAIN_PRIMES
        )
        self.tag_registry = PrimeRegistry.with_defaults(tag_primes or DEFAULT_TAG_PRIMES)
        self.records: Dict[str, MemoryRecord] = {}
        self._domain_index: Dict[str, set[str]] = {}

    def encode(
        self,
        domain: str,
        subdomain: str = "general",
        tags: Optional[Iterable[str]] = None,
        instance_key: Optional[str] = None,
    ) -> PrimeAddress:
        tag_values = sorted(self.tag_registry.normalize(tag) for tag in (tags or []))
        domain_norm = self.domain_registry.normalize(domain)
        subdomain_norm = self.subdomain_registry.normalize(subdomain)
        concept_source = "|".join(["concept", domain_norm, subdomain_norm, ",".join(tag_values)])
        concept = stable_instance_id(concept_source)
        instance_source = instance_key or "|".join([domain_norm, subdomain_norm, ",".join(tag_values)])
        return PrimeAddress(
            domain=self.domain_registry.get(domain_norm),
            subdomain=self.subdomain_registry.get(subdomain_norm),
            concept=concept,
            instance=stable_instance_id(instance_source),
        )

    def add(
        self,
        content: str,
        domain: str = "memory",
        subdomain: str = "general",
        tags: Optional[Iterable[str]] = None,
        vector: Optional[Iterable[float]] = None,
        importance: float = 0.5,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        instance_key: Optional[str] = None,
    ) -> MemoryRecord:
        tags_list = sorted({self.tag_registry.normalize(tag) for tag in (tags or [])})
        tag_product = self.tag_registry.product_for(tags_list)
        key = instance_key or content
        address = self.encode(domain, subdomain, tags_list, key).pack()
        record_id = f"{address:032x}"

        collision_counter = 1
        while record_id in self.records and self.records[record_id].content != content:
            address = self.encode(domain, subdomain, tags_list, f"{key}:{collision_counter}").pack()
            record_id = f"{address:032x}"
            collision_counter += 1

        now = utc_now()
        record = MemoryRecord(
            record_id=record_id,
            address=address,
            domain=self.domain_registry.normalize(domain),
            subdomain=self.subdomain_registry.normalize(subdomain),
            content=content,
            tags=tags_list,
            tag_product=tag_product,
            vector=as_float_vector(vector),
            importance=max(0.0, min(1.0, float(importance))),
            strength=max(0.0, min(1.0, float(strength))),
            created_at=now,
            updated_at=now,
            metadata=dict(metadata or {}),
        )

        self.records[record.record_id] = record
        self._domain_index.setdefault(record.domain, set()).add(record.record_id)
        return record

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self.records.get(record_id.lower().removeprefix("0x"))

    def query(
        self,
        domain: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        min_strength: float = 0.0,
        limit: int = 20,
        sort_results: bool = True,
    ) -> List[MemoryRecord]:
        if domain:
            normalized_domain = self.domain_registry.normalize(domain)
            # Domain index holds ids; materialize the (small) domain subset once.
            candidates: Iterable[MemoryRecord] = [
                self.records[record_id]
                for record_id in self._domain_index.get(normalized_domain, ())
            ]
        else:
            # No domain filter: scan record values directly, avoiding an O(n)
            # key-set copy plus per-id dict lookups.
            candidates = self.records.values()

        tag_values = sorted({self.tag_registry.normalize(tag) for tag in (tags or [])})
        if tag_values:
            tag_product = self.tag_registry.product_for_existing(tag_values)
            # An unknown query tag can match no record and must not register a
            # new prime on this read path, so short-circuit to an empty result.
            if tag_product is None:
                return []
        else:
            tag_product = 1

        apply_tag_filter = tag_product > 1
        results: List[MemoryRecord] = []
        for record in candidates:
            if record.strength < min_strength:
                continue
            if apply_tag_filter and not record.has_all_tag_primes(tag_product):
                continue
            results.append(record)

        # sort_results defaults to True to preserve best-first behavior; callers
        # can opt out (e.g. benchmarks, bulk filter-only paths) to skip the sort.
        if sort_results:
            results.sort(key=lambda record: (record.score(), record.updated_at), reverse=True)
        return results[:limit]

    def similar(
        self,
        vector: Iterable[float],
        domain: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        query_vector = as_float_vector(vector)
        candidates = self.query(domain=domain, tags=tags, limit=max(limit, len(self.records)))
        scored: List[Dict[str, Any]] = []
        for record in candidates:
            if not record.vector:
                continue
            similarity = cosine_similarity(query_vector, record.vector)
            scored.append({"record": record, "similarity": similarity})
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored[:limit]

    def remove(self, record_id: str) -> bool:
        key = record_id.lower().removeprefix("0x")
        record = self.records.pop(key, None)
        if not record:
            return False
        if record.domain in self._domain_index:
            self._domain_index[record.domain].discard(key)
        return True

    def stats(self) -> Dict[str, Any]:
        domains: Dict[str, int] = {}
        tags: Dict[str, int] = {}
        for record in self.records.values():
            domains[record.domain] = domains.get(record.domain, 0) + 1
            for tag in record.tags:
                tags[tag] = tags.get(tag, 0) + 1
        return {
            "records": len(self.records),
            "domains": dict(sorted(domains.items())),
            "tags": dict(sorted(tags.items())),
            "domain_primes": self.domain_registry.to_dict(),
            "subdomain_primes": self.subdomain_registry.to_dict(),
            "tag_primes": self.tag_registry.to_dict(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": "prime-memory-folding-store-v1",
            "domain_primes": self.domain_registry.to_dict(),
            "subdomain_primes": self.subdomain_registry.to_dict(),
            "tag_primes": self.tag_registry.to_dict(),
            "records": [record.to_dict() for record in self.records.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrimeMemoryStore":
        store = cls(
            domain_primes=dict(data.get("domain_primes", DEFAULT_DOMAIN_PRIMES)),
            subdomain_primes=dict(data.get("subdomain_primes", DEFAULT_SUBDOMAIN_PRIMES)),
            tag_primes=dict(data.get("tag_primes", DEFAULT_TAG_PRIMES)),
        )
        for entry in data.get("records", []):
            record = MemoryRecord.from_dict(entry)
            if "tag_product" not in entry:
                record.tag_product = store.tag_registry.product_for(record.tags)
            store.records[record.record_id] = record
            store._domain_index.setdefault(record.domain, set()).add(record.record_id)
        return store

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "PrimeMemoryStore":
        source = Path(path)
        if not source.exists():
            return cls()
        return cls.from_dict(json.loads(source.read_text(encoding="utf-8")))
