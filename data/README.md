# TicketSense data catalogue

This directory separates downloaded public research corpora from TicketSense-authored evaluation fixtures. Every external source must have a traceable upstream URL, license or usage terms, and checksum before it is used or redistributed.

| Data group | Repository location | Origin | Intended use |
|---|---|---|---|
| Public IT-support tickets | `data/external/public-it-support-tickets/` | Downloaded public corpus | Non-commercial routing/classification research |
| Synthetic knowledge base | `db/seed/knowledge_base/` | TicketSense-authored articles | Retrieval and grounded-answer evaluation |
| Screenshots and logs | `data/external/attachment-fixtures/` | Downloaded public research samples | OCR, parsing and attachment-ingestion demonstrations |

External data is not loaded automatically by Docker Compose. Application seed data remains under `db/seed/`, and existing import utilities remain opt-in.

### Public ticket corpus

The checked-in public corpus contains **28,587 records** in English and German. Its source fields include `subject`, `body`, `answer`, `type`, `queue`, `priority`, `language`, `version` and topic tags. It is useful for offline experiments involving ticket classification, priority prediction, queue routing and answer retrieval.

The corpus is licensed **CC BY-NC 4.0**, so it must not be used for commercial training or production deployment without separate permission. It is also broader than TicketSense's SAP, Networking, Cloud and HR taxonomy. Any experimental mapping must be measured and documented rather than silently treating upstream queues as equivalent departments.

The application does not train automatically from this file. A checked-in dataset proves reproducibility of an experiment; it does not prove that a deployed confidence score came from a trained model.

### Public attachment fixtures

`data/external/attachment-fixtures/` contains one 2,000-line Loghub HDFS sample and one CC0 terminal screenshot from GB82-SC. They provide stable inputs for log parsing, upload, preview and OCR integration tests without inventing company evidence.

Loghub describes its datasets as research/academic resources and requests repository attribution and paper citation. The HDFS sample is therefore not approved here for unrestricted commercial redistribution. GB82-SC is CC0, and its upstream license is preserved beside the screenshot. Detailed links and checksums are in the fixture README.

### Synthetic knowledge base

The 48 Markdown articles under `db/seed/knowledge_base/` are repository-authored evaluation content: 12 articles each for Cloud, HR, Networking and SAP. They are not scraped from a vendor knowledge portal and must not be presented as official SAP, cloud-provider, networking-vendor or HR policy documentation.

Their role is to test tenant-scoped retrieval, citations, answer grounding and knowledge-gap workflows. They are evaluation fixtures—not a pretrained model, not confidential enterprise data and not a replacement for reviewed operational procedures.

## Reproducibility checklist

Before using any external artifact:

1. Read its local README and upstream usage terms.
2. Recalculate SHA-256 with `Get-FileHash <path> -Algorithm SHA256` in PowerShell.
3. Confirm the hash matches the value recorded in the relevant README.
4. Keep non-commercial and research-only sources out of commercial model training.
5. Scan imported ticket text and attachments for privacy risks before exposing them to users or third-party AI providers.
6. Record any filtering, split, label mapping or normalization performed during an experiment.

Current external artifacts are intentionally disconnected from automatic startup. This prevents a normal `docker compose up` from silently importing research data into the application database.

## Bulk test data

## synthetic_labeled_tickets.py (current — use this one)

Inserts ~96 hand-authored tickets into `tickets`, 2 per `db/seed/knowledge_base/` article,
each phrased the way an end user would actually write it and labeled with the real
`department`/`priority`/`sentiment`. This is the training set for
`ai/models/train_classifier.py` — it exists because `import_helpdesk_tickets.py` below is
stale and has no sentiment field at all.

```
cd backend
uv sync --extra ai
uv run python ../data/synthetic_labeled_tickets.py           # inserts 96 tickets
uv run python ../data/synthetic_labeled_tickets.py --reset   # replace what's already there
```

Attributed to a placeholder `end_user` account (`synthetic-tickets@ticketsense.local`),
same cleanup pattern as below.

## import_helpdesk_tickets.py

> **Status: stale.** The department taxonomy changed from (IT Support, Billing,
> Engineering) to the real 4 departments (SAP, Networking, Cloud, HR). The
> `QUEUE_TO_DEPARTMENT` mapping below still targets the old 3 departments, so the script
> will fail at the "departments missing" check. This dataset's `queue` field doesn't have
> a real SAP category and its IT-ish queues are broader than our Networking/Cloud split,
> so it needs a proper remap (or a different source dataset) before reuse — not done here.
> `synthetic_labeled_tickets.py` above is the current source of ticket training data.

Pulls a sample of real ticket text into the `tickets` table so classification/RAG work
has more than the handful of structural seed rows from `db/seed/seed.sql` to run against.

### Source

[Tobi-Bueck/customer-support-tickets](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets)
on Hugging Face — 61,800 real-world-style customer support tickets, English and German,
licensed **CC-BY-NC-4.0** (non-commercial). Fine for this coursework/capstone use; don't
repurpose the imported rows commercially.

### Field mapping

| Dataset field | → | `tickets` column |
|---|---|---|
| `subject` | → | `subject` |
| `body` | → | `description` |
| `queue` | → | `department_id` (via the mapping below) |
| `priority` | → | `priority` (values already match our `low`/`medium`/`high`) |

`sentiment`, `ai_draft_reply`, `confidence_score`, and `confidence_features` are left
null — this script only backfills raw, unclassified ticket text for the
classification/retrieval pipeline to run against later.

### Why only some rows are imported

The dataset's `queue` field spans general customer support (billing, HR, sales,
returns, ...), not just IT. Only the queues below map cleanly onto TicketSense's old 3
seeded departments; everything else was filtered out rather than inventing new
departments to absorb it (this mapping is now stale — see the status note above):

| Dataset `queue` | → | TicketSense department |
|---|---|---|
| IT Support | → | IT Support |
| Technical Support | → | IT Support |
| Service Outages and Maintenance | → | IT Support |
| Billing and Payments | → | Billing |
| Product Support | → | Engineering |
| *(Customer Service, General Inquiry, Human Resources, Returns and Exchanges, Sales and Pre-Sales)* | | dropped |

Only `language == "en"` rows are imported.

### Usage (once the mapping is fixed)

```
cd backend
uv sync --extra ai
uv run python ../data/import_helpdesk_tickets.py            # imports 300 tickets
uv run python ../data/import_helpdesk_tickets.py --count 500
uv run python ../data/import_helpdesk_tickets.py --reset    # replace what's already imported
```

Imported tickets are attributed to a placeholder `end_user` account
(`bulk-import@ticketsense.local`, created automatically on first run) so they're
identifiable and easy to clean out later — `DELETE FROM tickets WHERE submitted_by =
(SELECT id FROM users WHERE email = 'bulk-import@ticketsense.local')`.

The dataset itself isn't committed to the repo — it's streamed from the Hugging Face
Hub each run (and cached locally by the `datasets` library under `~/.cache/huggingface`).
