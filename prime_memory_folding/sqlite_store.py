"""Optional SQLite persistence backend for Prime Memory Folding.

Uses only the standard-library ``sqlite3`` module (no new dependencies). JSON
remains the default store format; SQLite is opt-in.

Storage note (important): a record's packed ``address`` is 128-bit and its
``tag_product`` is an unbounded Python integer. Both can exceed SQLite's signed
64-bit INTEGER, so they are persisted as TEXT (decimal strings) and parsed back
with ``int()``. The rest of the columns are plain values or JSON text.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Union

from .primes import DEFAULT_DOMAIN_PRIMES, DEFAULT_SUBDOMAIN_PRIMES, DEFAULT_TAG_PRIMES
from .store import MemoryRecord, PrimeMemoryStore, parse_dt

SCHEMA_FORMAT = "prime-memory-folding-sqlite-v1"

PathLike = Union[str, Path]


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS registries (
            kind  TEXT,
            label TEXT,
            prime INTEGER,
            PRIMARY KEY (kind, label)
        );
        CREATE TABLE IF NOT EXISTS records (
            record_id   TEXT PRIMARY KEY,
            address     TEXT,
            domain      TEXT,
            subdomain   TEXT,
            content     TEXT,
            tags        TEXT,
            tag_product TEXT,
            vector      TEXT,
            importance  REAL,
            strength    REAL,
            created_at  TEXT,
            updated_at  TEXT,
            metadata    TEXT
        );
        """
    )


def save_store_to_sqlite(store: PrimeMemoryStore, path: PathLike) -> None:
    """Persist the full store (records + prime registries) to a SQLite file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    try:
        _init_schema(conn)
        conn.execute("DELETE FROM meta")
        conn.execute("DELETE FROM registries")
        conn.execute("DELETE FROM records")
        conn.execute("INSERT INTO meta(key, value) VALUES(?, ?)", ("format", SCHEMA_FORMAT))

        for kind, registry in (
            ("domain", store.domain_registry),
            ("subdomain", store.subdomain_registry),
            ("tag", store.tag_registry),
        ):
            conn.executemany(
                "INSERT INTO registries(kind, label, prime) VALUES(?, ?, ?)",
                [(kind, label, prime) for label, prime in registry.to_dict().items()],
            )

        conn.executemany(
            """
            INSERT INTO records(
                record_id, address, domain, subdomain, content, tags, tag_product,
                vector, importance, strength, created_at, updated_at, metadata
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    record.record_id,
                    str(record.address),          # 128-bit -> TEXT
                    record.domain,
                    record.subdomain,
                    record.content,
                    json.dumps(record.tags),
                    str(record.tag_product),      # unbounded -> TEXT
                    json.dumps(record.vector),
                    record.importance,
                    record.strength,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    json.dumps(record.metadata),
                )
                for record in store.records.values()
            ],
        )
        conn.commit()
    finally:
        conn.close()


def load_store_from_sqlite(path: PathLike) -> PrimeMemoryStore:
    """Load a store from a SQLite file. Returns an empty store if it is absent."""
    source = Path(path)
    if not source.exists():
        return PrimeMemoryStore()

    conn = sqlite3.connect(str(source))
    try:
        _init_schema(conn)  # tolerate a fresh/empty file
        registries = {"domain": {}, "subdomain": {}, "tag": {}}
        for kind, label, prime in conn.execute("SELECT kind, label, prime FROM registries"):
            registries.setdefault(kind, {})[label] = int(prime)

        store = PrimeMemoryStore(
            domain_primes=registries["domain"] or dict(DEFAULT_DOMAIN_PRIMES),
            subdomain_primes=registries["subdomain"] or dict(DEFAULT_SUBDOMAIN_PRIMES),
            tag_primes=registries["tag"] or dict(DEFAULT_TAG_PRIMES),
        )

        rows = conn.execute(
            """
            SELECT record_id, address, domain, subdomain, content, tags, tag_product,
                   vector, importance, strength, created_at, updated_at, metadata
            FROM records
            """
        )
        for row in rows:
            (
                record_id, address, domain, subdomain, content, tags, tag_product,
                vector, importance, strength, created_at, updated_at, metadata,
            ) = row
            record = MemoryRecord(
                record_id=record_id,
                address=int(address),
                domain=domain,
                subdomain=subdomain,
                content=content,
                tags=list(json.loads(tags)),
                tag_product=int(tag_product),
                vector=[float(value) for value in json.loads(vector)],
                importance=float(importance),
                strength=float(strength),
                created_at=parse_dt(created_at),
                updated_at=parse_dt(updated_at),
                metadata=dict(json.loads(metadata)),
            )
            store.records[record.record_id] = record
            store._domain_index.setdefault(record.domain, set()).add(record.record_id)
        return store
    finally:
        conn.close()


def migrate_json_to_sqlite(json_path: PathLike, sqlite_path: PathLike) -> PrimeMemoryStore:
    """Load a JSON store and write it to SQLite. Returns the migrated store."""
    store = PrimeMemoryStore.load(json_path)
    save_store_to_sqlite(store, sqlite_path)
    return store


def export_sqlite_to_json(sqlite_path: PathLike, json_path: PathLike) -> PrimeMemoryStore:
    """Load a SQLite store and write it back out as JSON. Returns the store."""
    store = load_store_from_sqlite(sqlite_path)
    store.save(json_path)
    return store
