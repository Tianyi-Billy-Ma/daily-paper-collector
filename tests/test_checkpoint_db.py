import sqlite3

from scripts.checkpoint_db import compact_database


def test_compact_database_removes_expired_embeddings_and_reclaims_space(tmp_path) -> None:
    db_path = tmp_path / "papers.db"
    embedding = bytes(2 * 1024 * 1024)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE papers (id INTEGER PRIMARY KEY, created_at TEXT, embedding BLOB)"
        )
        conn.executemany(
            "INSERT INTO papers (created_at, embedding) VALUES (?, ?)",
            [
                ("2000-01-01 00:00:00", embedding),
                ("2000-01-02 00:00:00", embedding),
                ("2999-01-01 00:00:00", embedding),
            ],
        )

    size_before = db_path.stat().st_size

    compact_database(db_path, embedding_retention_days=30)

    with sqlite3.connect(db_path) as conn:
        embeddings = conn.execute("SELECT embedding FROM papers ORDER BY created_at").fetchall()

    assert embeddings == [(None,), (None,), (embedding,)]
    assert db_path.stat().st_size < size_before / 2
