"""Runs a few sample tickets through the two real LangGraph stages (classify, retrieve)
— draft/score are stubs, so this calls the node functions directly rather than
invoking the full compiled graph. Proof that classification and retrieval work
together before the rest of the pipeline exists.

Usage (from backend/):
    uv sync --extra ai
    uv run python ../ai/graph/run_example.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ai.graph.nodes import classify_node, retrieve_node  # noqa: E402

SAMPLE_TICKETS = [
    {
        "subject": "Can't post goods receipt - ME023 error",
        "description": "Getting error ME023 'item is blocked' when I try to do a goods "
        "receipt in MIGO for PO 4500012345. This is holding up our receiving dock.",
    },
    {
        "subject": "VPN won't connect from home",
        "description": "Working from home today and VPN just hangs on Connecting and "
        "never gets in. I have a client call in an hour and need internal access.",
    },
    {
        "subject": "App getting Access Denied from S3",
        "description": "Our production service just started throwing Access Denied "
        "errors reading from the reports bucket. This is affecting live customer reports.",
    },
    {
        "subject": "How many vacation days do I get?",
        "description": "I'm trying to plan a trip next year and wanted to confirm how "
        "many annual leave days I'm entitled to.",
    },
]


async def main() -> None:
    for ticket in SAMPLE_TICKETS:
        state = {"subject": ticket["subject"], "description": ticket["description"]}
        state.update(await classify_node(state))
        state.update(await retrieve_node(state))

        print(f"\nTicket: {ticket['subject']!r}")
        print(
            f"  Predicted -> department={state['department']} "
            f"priority={state['priority']} sentiment={state['sentiment']}"
        )
        chunks = state.get("retrieved_chunks") or []
        if chunks:
            top = chunks[0]
            print(f"  Top retrieved article: {top['title']!r} (distance={top['distance']:.4f})")
        else:
            print("  No article retrieved.")


if __name__ == "__main__":
    asyncio.run(main())
