import datetime
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional
from storage.models import Item


class Database:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, params=()):
        """Open a connection, execute, commit, close, and return cursor."""
        conn = self._connect()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def _fetchall(self, sql: str, params=()):
        """Open a connection, fetch all rows, close, and return rows."""
        conn = self._connect()
        try:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def _fetchone(self, sql: str, params=()):
        """Open a connection, fetch one row, close, and return row."""
        conn = self._connect()
        try:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()
        finally:
            conn.close()

    def init(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    summary TEXT,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_items_category
                ON items(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_items_published
                ON items(published_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def insert(self, item: Item) -> Item:
        cursor = self._execute(
            """INSERT INTO items (title, source, url, category, summary, published_at, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                item.title, item.source, item.url, item.category,
                item.summary,
                item.published_at.isoformat(),
                item.fetched_at.isoformat(),
            ),
        )
        item.id = cursor.lastrowid
        return item

    def exists_by_url(self, url: str) -> bool:
        row = self._fetchone("SELECT 1 FROM items WHERE url = ?", (url,))
        return row is not None

    def query_recent(self, days: int = 7) -> list[Item]:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        rows = self._fetchall(
            "SELECT * FROM items WHERE published_at >= ? ORDER BY published_at DESC",
            (cutoff,),
        )
        return [self._row_to_item(r) for r in rows]

    def query_by_category(self, category: str, days: int = 7) -> list[Item]:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        rows = self._fetchall(
            "SELECT * FROM items WHERE category = ? AND published_at >= ? ORDER BY published_at DESC",
            (category, cutoff),
        )
        return [self._row_to_item(r) for r in rows]

    def query_without_summary(self, limit: int = 50) -> list[Item]:
        rows = self._fetchall(
            "SELECT * FROM items WHERE summary IS NULL ORDER BY published_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_item(r) for r in rows]

    def update_summary(self, item_id: int, summary: str) -> None:
        self._execute(
            "UPDATE items SET summary = ? WHERE id = ?",
            (summary, item_id),
        )

    def cleanup(self, days: int = 14) -> int:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        cursor = self._execute(
            "DELETE FROM items WHERE published_at < ?", (cutoff,)
        )
        return cursor.rowcount

    def _row_to_item(self, row: sqlite3.Row) -> Item:
        return Item(
            id=row["id"],
            title=row["title"],
            source=row["source"],
            url=row["url"],
            category=row["category"],
            summary=row["summary"],
            published_at=datetime.datetime.fromisoformat(row["published_at"]),
            fetched_at=datetime.datetime.fromisoformat(row["fetched_at"]),
        )
