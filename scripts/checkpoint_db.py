"""Flush SQLite WAL changes into the main database file for Git commits."""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Final

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config

DEFAULT_EMBEDDING_RETENTION_DAYS: Final = 30


def compact_database(db_path: Path, embedding_retention_days: int) -> int:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA journal_mode=DELETE")
        result = conn.execute(
            "UPDATE papers "
            "SET embedding = NULL "
            "WHERE embedding IS NOT NULL "
            "AND created_at < datetime('now', ?)",
            (f"-{embedding_retention_days} days",),
        )
        conn.commit()
        conn.execute("VACUUM")
        return result.rowcount
    finally:
        conn.close()


def main() -> None:
    config = load_config()
    db_path = Path(config["database"]["path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"No database found at {db_path}; nothing to checkpoint.")
        return

    removed_embeddings = compact_database(db_path, DEFAULT_EMBEDDING_RETENTION_DAYS)
    print(
        f"Checkpointed database at {db_path}; removed {removed_embeddings} expired paper embeddings"
    )


if __name__ == "__main__":
    main()
