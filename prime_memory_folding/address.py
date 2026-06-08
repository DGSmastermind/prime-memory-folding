"""Prime-address packing utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

U32_MAX = (1 << 32) - 1


def _check_u32(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0 or value > U32_MAX:
        raise ValueError(f"{name} must fit in unsigned 32 bits")
    return value


def stable_instance_id(value: str) -> int:
    """Return a stable 32-bit instance id for a string key."""
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big")


@dataclass(frozen=True)
class PrimeAddress:
    """A 128-bit address split into four 32-bit lanes.

    The lanes are intentionally generic:
    - domain: broad namespace prime
    - subdomain: narrower namespace prime
    - concept: compact 32-bit identity or bucket
    - instance: stable 32-bit id
    """

    domain: int
    subdomain: int
    concept: int
    instance: int

    def __post_init__(self) -> None:
        _check_u32("domain", self.domain)
        _check_u32("subdomain", self.subdomain)
        _check_u32("concept", self.concept)
        _check_u32("instance", self.instance)

    def pack(self) -> int:
        return (
            (self.domain << 96)
            | (self.subdomain << 64)
            | (self.concept << 32)
            | self.instance
        )

    @classmethod
    def unpack(cls, packed: int) -> "PrimeAddress":
        if packed < 0 or packed > ((1 << 128) - 1):
            raise ValueError("packed address must fit in unsigned 128 bits")
        return cls(
            domain=(packed >> 96) & U32_MAX,
            subdomain=(packed >> 64) & U32_MAX,
            concept=(packed >> 32) & U32_MAX,
            instance=packed & U32_MAX,
        )

    def has_all_tag_primes(self, tag_product: int, stored_tag_product: Optional[int] = None) -> bool:
        """Return true when the stored tag product contains all query primes.

        The packed concept lane is only 32 bits, so callers with real tag
        products should pass the record's unbounded ``stored_tag_product``.
        Falling back to ``self.concept`` preserves compatibility for compact
        toy addresses and old tests.
        """
        if tag_product <= 1:
            return True
        candidate = self.concept if stored_tag_product is None else stored_tag_product
        return candidate % tag_product == 0

    def to_hex(self) -> str:
        return f"0x{self.pack():032x}"

    @classmethod
    def from_hex(cls, value: str) -> "PrimeAddress":
        cleaned = value.lower().removeprefix("0x")
        return cls.unpack(int(cleaned, 16))
