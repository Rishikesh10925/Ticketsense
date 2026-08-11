"""Imports a sample of real IT-helpdesk tickets from the public
Tobi-Bueck/customer-support-tickets Hugging Face dataset into the `tickets`
table, so classification/RAG work has realistic text to run against instead
of just the handful of structural seed rows from db/seed/seed.sql.

Requires the `data` extra and a migrated + seeded database:
    cd backend
    uv sync --extra ai
    uv run alembic upgrade head            # if not already applied
    uv run python ../db/seed/run_seed.py   # needs the department rows
    uv run python ../data/import_helpdesk_tickets.py [--count 300] [--reset]

Source dataset: https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets
License: CC-BY-NC-4.0 (non-commercial) — fine for this coursework/capstone use;
don't repurpose the imported rows commercially.

See data/README.md for the queue -> department mapping and why most of the
dataset's queues are dropped rather than imported.
"""

import argparse
import asyncio
import re
from pathlib import Path
from uuid import UUID

import asyncpg
from datasets import load_dataset
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
DATASET_NAME = "Tobi-Bueck/customer-support-tickets"
BULK_IMPORT_EMAIL = "bulk-import@ticketsense.local"

# The dataset's `queue` field spans general customer support, not just IT.
# Only the queues that map cleanly onto our 3 seeded departments are kept;
# everything else (Customer Service, General Inquiry, Human Resources,
# Returns and Exchanges, Sales and Pre-Sales) is dropped rather than
# inventing new departments to absorb it.
QUEUE_TO_DEPARTMENT = {
    "IT Support": "IT Support",
    "Technical Support": "IT Support",
    "Service Outages and Maintenance": "IT Support",
    "Billing and Payments": "Billing",
    "Product Support": "Engineering",
}


def _asyncpg_url(database_url: str) -> str:
    return re.sub(r"^postgresql\+asyncpg://", "postgresql://", database_url)


def load_sample(count: int, seed: int = 42) -> list[dict]:
    dataset = load_dataset(DATASET_NAME, split="train")
    dataset = dataset.filter(
        lambda row: (
            row["language"] == "en"
            and row["queue"] in QUEUE_TO_DEPARTMENT
            and (row["subject"] or "").strip()
            and (row["body"] or "").strip()
        )
    )
    dataset = dataset.shuffle(seed=seed)
    count = min(count, len(dataset))
    rows = dataset.select(range(count))

    return [
        {
            "subject": row["subject"],
            "description": row["body"],
            "department": QUEUE_TO_DEPARTMENT[row["queue"]],
            "priority": row["priority"],
        }
        for row in rows
    ]


async def get_or_create_bulk_import_user(conn: asyncpg.Connection) -> UUID:
    user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", BULK_IMPORT_EMAIL)
    if user_id:
        return user_id
    return await conn.fetchval(
        """
        INSERT INTO users (email, full_name, role, hashed_password)
        VALUES ($1, 'Bulk Import', 'end_user', 'CHANGE_ME_dev_placeholder')
        RETURNING id
        """,
        BULK_IMPORT_EMAIL,
    )


async def get_department_ids(conn: asyncpg.Connection) -> dict[str, UUID]:
    rows = await conn.fetch("SELECT id, name FROM departments")
    ids = {row["name"]: row["id"] for row in rows}
    missing = set(QUEUE_TO_DEPARTMENT.values()) - set(ids)
    if missing:
        raise SystemExit(
            f"Departments missing from the database: {sorted(missing)}. "
            "Run db/seed/seed.sql first (uv run python ../db/seed/run_seed.py)."
        )
    return ids


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=300, help="Number of tickets to import")
    parser.add_argument(
        "--reset", action="store_true", help="Delete previously bulk-imported tickets first"
    )
    args = parser.parse_args()

    env = dotenv_values(ROOT / ".env")
    database_url = env.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set — copy .env.example to .env first.")

    print(f"Loading and sampling up to {args.count} tickets from {DATASET_NAME}...")
    sample = load_sample(args.count)
    print(f"Sampled {len(sample)} English tickets across {len(QUEUE_TO_DEPARTMENT)} mapped queues.")

    conn = await asyncpg.connect(_asyncpg_url(database_url))
    try:
        bulk_user_id = await get_or_create_bulk_import_user(conn)
        department_ids = await get_department_ids(conn)

        existing = await conn.fetchval(
            "SELECT count(*) FROM tickets WHERE submitted_by = $1", bulk_user_id
        )
        if existing and args.reset:
            await conn.execute("DELETE FROM tickets WHERE submitted_by = $1", bulk_user_id)
            print(f"--reset: removed {existing} previously imported tickets.")
        elif existing:
            print(
                f"{existing} bulk-imported tickets already present, skipping "
                "(pass --reset to replace them)."
            )
            return

        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO tickets (submitted_by, department_id, subject, description, priority)
                VALUES ($1, $2, $3, $4, $5)
                """,
                [
                    (
                        bulk_user_id,
                        department_ids[row["department"]],
                        row["subject"],
                        row["description"],
                        row["priority"],
                    )
                    for row in sample
                ],
            )
        print(f"Inserted {len(sample)} tickets.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
