"""Memory decay and folding."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Sequence

from .store import MemoryRecord, PrimeMemoryStore
from .vectors import cosine_similarity, weighted_average


@dataclass
class FoldingPolicy:
    """Controls decay, clustering, and folded-memory creation."""

    similarity_threshold: float = 0.82
    minimum_strength: float = 0.05
    folded_importance_boost: float = 0.08
    max_summary_items: int = 5
    decay_rates_per_hour: Dict[str, float] = field(
        default_factory=lambda: {
            "working": 0.10,
            "short_term": 0.02,
            "long_term": 0.001,
            "permanent": 0.0,
            "eternal": 0.0,
        }
    )


@dataclass
class FoldResult:
    """Result of a folding pass."""

    scanned: int
    folded: int
    pruned: int
    created: List[MemoryRecord]
    pruned_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanned": self.scanned,
            "folded": self.folded,
            "pruned": self.pruned,
            "created": [record.to_dict() for record in self.created],
            "pruned_ids": self.pruned_ids,
        }


class MemoryFolder:
    """Consolidates similar memory records into compact folded records."""

    def __init__(self, policy: FoldingPolicy | None = None) -> None:
        self.policy = policy or FoldingPolicy()

    def _tier_for(self, record: MemoryRecord) -> str:
        explicit = str(record.metadata.get("tier", "")).lower()
        if explicit in self.policy.decay_rates_per_hour:
            return explicit
        if record.importance >= 0.95:
            return "eternal"
        if record.importance >= 0.75:
            return "long_term"
        if record.importance >= 0.4:
            return "short_term"
        return "working"

    def decay_strength(self, record: MemoryRecord, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        elapsed_hours = max(0.0, (now - record.updated_at).total_seconds() / 3600)
        rate = self.policy.decay_rates_per_hour[self._tier_for(record)]
        if rate <= 0:
            return record.strength
        return max(0.0, record.strength * ((1 - rate) ** elapsed_hours))

    def apply_decay(self, store: PrimeMemoryStore, now: datetime | None = None) -> List[str]:
        pruned_ids: List[str] = []
        for record in list(store.records.values()):
            record.strength = self.decay_strength(record, now)
            if record.strength < self.policy.minimum_strength:
                pruned_ids.append(record.record_id)
        for record_id in pruned_ids:
            store.remove(record_id)
        return pruned_ids

    def fold_store(self, store: PrimeMemoryStore) -> FoldResult:
        scanned = len(store.records)
        pruned_ids = self.apply_decay(store)
        clusters = self._cluster_records(list(store.records.values()))
        created: List[MemoryRecord] = []
        folded_source_ids: set[str] = set()

        for cluster in clusters:
            if len(cluster) < 2:
                continue
            folded = self._create_folded_record(store, cluster)
            created.append(folded)
            folded_source_ids.update(record.record_id for record in cluster)

        for record_id in folded_source_ids:
            store.remove(record_id)

        return FoldResult(
            scanned=scanned,
            folded=len(folded_source_ids),
            pruned=len(pruned_ids),
            created=created,
            pruned_ids=pruned_ids,
        )

    def _cluster_records(self, records: Sequence[MemoryRecord]) -> List[List[MemoryRecord]]:
        clusters: List[List[MemoryRecord]] = []
        used: set[str] = set()
        vector_records = [record for record in records if record.vector]

        for record in vector_records:
            if record.record_id in used:
                continue
            cluster = [record]
            used.add(record.record_id)
            for candidate in vector_records:
                if candidate.record_id in used:
                    continue
                if not self._compatible(record, candidate):
                    continue
                if cosine_similarity(record.vector, candidate.vector) >= self.policy.similarity_threshold:
                    cluster.append(candidate)
                    used.add(candidate.record_id)
            clusters.append(cluster)

        for record in records:
            if record.record_id not in used:
                clusters.append([record])
        return clusters

    def _compatible(self, left: MemoryRecord, right: MemoryRecord) -> bool:
        if left.domain != right.domain:
            return False
        if left.subdomain == right.subdomain:
            return True
        return bool(set(left.tags).intersection(right.tags))

    def _create_folded_record(
        self,
        store: PrimeMemoryStore,
        cluster: Sequence[MemoryRecord],
    ) -> MemoryRecord:
        weights = [max(0.01, record.score()) for record in cluster]
        vector = weighted_average([record.vector for record in cluster], weights)
        tags = sorted(set().union(*(set(record.tags) for record in cluster), {"folded"}))
        importance = min(
            1.0,
            max(record.importance for record in cluster) + self.policy.folded_importance_boost,
        )
        strength = min(1.0, sum(record.strength for record in cluster) / len(cluster) + 0.05)
        content = self._summarize(cluster)
        metadata = {
            "tier": "long_term" if importance >= 0.75 else "short_term",
            "folded_from": [record.record_id for record in cluster],
            "folded_count": len(cluster),
            "source_domains": sorted({record.domain for record in cluster}),
        }
        return store.add(
            content=content,
            domain=cluster[0].domain,
            subdomain=cluster[0].subdomain,
            tags=tags,
            vector=vector,
            importance=importance,
            strength=strength,
            metadata=metadata,
            instance_key="fold:" + "|".join(record.record_id for record in cluster),
        )

    def _summarize(self, records: Iterable[MemoryRecord]) -> str:
        records_list = list(records)
        snippets = []
        for record in records_list[: self.policy.max_summary_items]:
            cleaned = " ".join(record.content.split())
            snippets.append(cleaned[:180])
        return "Folded memory from " + str(len(records_list)) + " related records: " + " | ".join(snippets)
