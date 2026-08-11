"""drop undersized ivfflat index on embeddings

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-09

The ivfflat index was created with `lists = 100`, but the embeddings table currently
holds only a few dozen rows — well under 1 row per list on average. With the default
`probes = 1`, ivfflat searches a single near-empty cluster, so queries return
incomplete and often wrong results (confirmed empirically: a query for "ME023 error"
missed the ME023 article entirely when going through this index, but found it
correctly once the index was removed and Postgres fell back to an exact scan).

ivfflat only pays off once the table has enough rows that a sequential scan is
actually slow (tens of thousands+) and `lists` is tuned to the real row count. Until
then, no index at all gives exact, correct results and is plenty fast — pgvector's
`<=>` operator works fine without an index, it just does a full scan. Revisit this
once the embeddings table is large enough to need one.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embeddings_embedding_ivfflat")


def downgrade() -> None:
    op.execute(
        "CREATE INDEX ix_embeddings_embedding_ivfflat ON embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
