"""Loads the curated Markdown KB articles under db/seed/knowledge_base/ into the
knowledge_base table. Each department is a subfolder (sap/, networking/, cloud/, hr/)
whose name must match db/seed/seed.sql's department names case-insensitively; each
.md file in it becomes one knowledge_base row, title taken from the file's leading
"# " heading.

Requires seed.sql to have been applied first (needs the 4 department rows).

Usage (from backend/):
    uv run python ../db/seed/load_knowledge_base.py [--reset]
"""

import argparse
import asyncio
import os
import re
from pathlib import Path
from uuid import UUID

import asyncpg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
KB_DIR = Path(__file__).resolve().parent / "knowledge_base"

# Folder name -> department name in the `departments` table.
DEPARTMENT_NAMES = {
    "sap": "SAP",
    "networking": "Networking",
    "cloud": "Cloud",
    "hr": "HR",
}


def _asyncpg_url(database_url: str) -> str:
    return re.sub(r"^postgresql\+asyncpg://", "postgresql://", database_url)


def _parse_article(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"#\s+(.+?)\s*\n", text)
    if not match:
        raise ValueError(f"{path} has no leading '# Title' heading")
    return match.group(1), text


def load_articles() -> list[dict]:
    articles = []
    for folder, department in DEPARTMENT_NAMES.items():
        dept_dir = KB_DIR / folder
        if not dept_dir.is_dir():
            raise SystemExit(f"Expected KB folder missing: {dept_dir}")
        md_files = sorted(dept_dir.glob("*.md"))
        if not md_files:
            raise SystemExit(f"No .md articles found under {dept_dir}")
        for path in md_files:
            title, content = _parse_article(path)
            articles.append({"department": department, "title": title, "content": content})
    return articles


async def get_department_ids(conn: asyncpg.Connection) -> dict[str, UUID]:
    rows = await conn.fetch("SELECT id, name FROM departments")
    ids = {row["name"]: row["id"] for row in rows}
    missing = set(DEPARTMENT_NAMES.values()) - set(ids)
    if missing:
        raise SystemExit(
            f"Departments missing from the database: {sorted(missing)}. "
            "Run db/seed/seed.sql first (uv run python ../db/seed/run_seed.py)."
        )
    return ids


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset", action="store_true", help="Delete all existing knowledge_base rows first"
    )
    args = parser.parse_args()

    env = dotenv_values(ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL") or env.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set — copy .env.example to .env first.")

    articles = load_articles()
    print(f"Loaded {len(articles)} articles from {KB_DIR}.")

    conn = await asyncpg.connect(_asyncpg_url(database_url))
    try:
        department_ids = await get_department_ids(conn)
        tenant_id = await conn.fetchval("SELECT id FROM organizations WHERE slug='ticketsense-demo'")

        existing = await conn.fetchval("SELECT count(*) FROM knowledge_base")
        if existing and not args.reset:
            print(
                f"{existing} knowledge_base rows already present, skipping "
                "(pass --reset to replace them)."
            )
            return

        async with conn.transaction():
            if existing:
                await conn.execute("DELETE FROM knowledge_base")
                print(f"--reset: removed {existing} existing knowledge_base rows.")

            await conn.executemany(
                """
                INSERT INTO knowledge_base (department_id, title, content, tenant_id)
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (department_ids[a["department"]], a["title"], a["content"], tenant_id)
                    for a in articles
                ],
            )
        print(f"Inserted {len(articles)} knowledge_base articles.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
