from prime_memory_folding import PrimeMemorySystem


system = PrimeMemorySystem(".prime_memory_folding/example-store.json")

system.remember(
    "Prime encoding is ideal for hot-path domain and tag filters.",
    domain="architecture",
    subdomain="decision",
    tags=["prime", "technical", "standalone"],
    vector=[0.95, 0.15, 0.2],
    importance=0.9,
)

system.remember(
    "Vector stores remain necessary for semantic similarity.",
    domain="architecture",
    subdomain="decision",
    tags=["vector", "technical", "standalone"],
    vector=[0.9, 0.2, 0.25],
    importance=0.85,
)

print(system.recall(domain="architecture", tags=["technical"], limit=5))
print(system.fold().to_dict())
