import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from src.scraper.models import Recipe

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
    site TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    http_status INTEGER,
    fetched_at TEXT,
    PRIMARY KEY (site, recipe_id)
);
CREATE TABLE IF NOT EXISTS recipes (
    site TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    url TEXT NOT NULL,
    name TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    total_minutes INTEGER,
    kcal_per_100g REAL,
    servings INTEGER,
    PRIMARY KEY (site, recipe_id)
);
"""


class Storage:
    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, timeout=30)
        self.conn.executescript(SCHEMA)

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *exc) -> None:
        self.conn.close()

    def add_urls(
        self, site: str, items: Iterable[tuple[str, str]], batch_size: int = 500
    ) -> int:
        added = 0
        batch: list[tuple[str, str, str]] = []
        for recipe_id, url in items:
            batch.append((site, recipe_id, url))
            if len(batch) >= batch_size:
                added += self._insert(batch)
                batch.clear()
        if batch:
            added += self._insert(batch)
        return added

    def _insert(self, rows: list[tuple[str, str, str]]) -> int:
        cursor = self.conn.executemany(
            "INSERT OR IGNORE INTO urls (site, recipe_id, url) VALUES (?, ?, ?)",
            rows,
        )
        self.conn.commit()
        return cursor.rowcount

    def count_by_status(self) -> list[tuple[str, str, int]]:
        return self.conn.execute(
            "SELECT site, status, COUNT(*) FROM urls GROUP BY site, status"
        ).fetchall()
    def pending(self, site: str, limit: int) -> list[tuple[str, str]]:
        return self.conn.execute(
            "SELECT recipe_id, url FROM urls "
            "WHERE site = ? AND status = 'new' ORDER BY RANDOM() LIMIT ?",
            (site, limit),
        ).fetchall()
    def downloaded(self, site: str, reparse: bool = False) -> list[tuple[str, str]]:
        statuses = ("downloaded", "parsed", "parse_failed") if reparse else (
            "downloaded",
        )
        placeholders = ", ".join("?" for _ in statuses)
        return self.conn.execute(
            f"SELECT recipe_id, url FROM urls "
            f"WHERE site = ? AND status IN ({placeholders})",
            (site, *statuses),
        ).fetchall()

    def set_status(self, site: str, recipe_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE urls SET status = ? WHERE site = ? AND recipe_id = ?",
            (status, site, recipe_id),
        )
        self.conn.commit()

    def save_recipe(self, recipe: Recipe) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO recipes "
            "(site, recipe_id, url, name, ingredients, total_minutes, kcal_per_100g, "
            "servings) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                recipe.site,
                recipe.recipe_id,
                recipe.url,
                recipe.name,
                json.dumps(recipe.ingredients, ensure_ascii=False),
                recipe.total_minutes,
                recipe.kcal_per_100g,
                recipe.servings,
            ),
        )
        self.set_status(recipe.site, recipe.recipe_id, "parsed")
    def mark(
        self, site: str, recipe_id: str, status: str, http_status: int | None = None
    ) -> None:
        self.conn.execute(
            "UPDATE urls SET status = ?, http_status = ?, fetched_at = ? "
            "WHERE site = ? AND recipe_id = ?",
            (
                status,
                http_status,
                datetime.now(timezone.utc).isoformat(),
                site,
                recipe_id,
            ),
        )
        self.conn.commit()    