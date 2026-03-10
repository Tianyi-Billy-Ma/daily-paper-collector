"""Flush SQLite WAL changes into the main database file for Git commits."""

import sqlite3
from pathlib import Path

from src.config import load_config


def main():
    config = load_config()
    db_path = Path(config["database"]["path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"No database found at {db_path}; nothing to checkpoint.")
        return

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA journal_mode=DELETE")
    finally:
        conn.close()

    print(f"Checkpointed database at {db_path}")


if __name__ == "__main__":
    main()
