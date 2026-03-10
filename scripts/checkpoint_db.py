"""Flush SQLite WAL changes into the main database file for Git commits."""

import os
import sqlite3
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
