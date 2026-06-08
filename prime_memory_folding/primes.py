"""Prime registries for address fields and tag products."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


DEFAULT_DOMAIN_PRIMES: Dict[str, int] = {
    "memory": 2,
    "project": 3,
    "file": 5,
    "symbol": 7,
    "decision": 11,
    "task": 13,
    "session": 17,
    "metric": 19,
    "workflow": 23,
    "agent": 29,
}

DEFAULT_SUBDOMAIN_PRIMES: Dict[str, int] = {
    "general": 2,
    "episodic": 3,
    "semantic": 5,
    "procedural": 7,
    "reflection": 11,
    "code": 13,
    "document": 17,
    "architecture": 19,
    "decision": 23,
    "test": 29,
}

DEFAULT_TAG_PRIMES: Dict[str, int] = {
    "important": 2,
    "recent": 3,
    "source": 5,
    "technical": 7,
    "architecture": 11,
    "code": 13,
    "evidence": 17,
    "folded": 19,
    "standalone": 23,
    "ide": 29,
}


def is_prime(value: int) -> bool:
    """Return true if value is prime."""
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def next_prime(after: int) -> int:
    """Return the first prime greater than after."""
    candidate = max(2, after + 1)
    while not is_prime(candidate):
        candidate += 1
    return candidate


def prime_product(values: Iterable[int]) -> int:
    """Return the product of prime values, or 1 for an empty iterable."""
    product = 1
    for value in values:
        product *= value
    return product


@dataclass
class PrimeRegistry:
    """Mutable label to prime registry.

    Labels are normalized to lowercase strings. Existing labels keep their
    assigned prime forever, which keeps stored addresses stable.
    """

    mapping: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def with_defaults(cls, defaults: Dict[str, int]) -> "PrimeRegistry":
        return cls(dict(defaults))

    def normalize(self, label: str) -> str:
        normalized = label.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("prime registry labels cannot be empty")
        return normalized

    def get(self, label: str) -> int:
        normalized = self.normalize(label)
        if normalized not in self.mapping:
            highest = max(self.mapping.values(), default=1)
            self.mapping[normalized] = next_prime(highest)
        return self.mapping[normalized]

    def product_for(self, labels: Iterable[str]) -> int:
        return prime_product(self.get(label) for label in labels)

    def get_existing(self, label: str) -> Optional[int]:
        """Return the prime for an already-registered label, or None.

        Unlike :meth:`get`, this never assigns a new prime, so it is safe to
        call on read paths (queries) without mutating the registry.
        """
        return self.mapping.get(self.normalize(label))

    def product_for_existing(self, labels: Iterable[str]) -> Optional[int]:
        """Return the prime product for labels, or None if any are unknown.

        Non-mutating: an unknown label yields ``None`` instead of registering a
        new prime. Callers treat ``None`` as a guaranteed non-match.
        """
        product = 1
        for label in labels:
            prime = self.get_existing(label)
            if prime is None:
                return None
            product *= prime
        return product

    def labels_for_product(self, product: int) -> List[str]:
        labels: List[str] = []
        for label, prime in self.mapping.items():
            if product % prime == 0:
                labels.append(label)
        return sorted(labels)

    def to_dict(self) -> Dict[str, int]:
        return dict(sorted(self.mapping.items()))
