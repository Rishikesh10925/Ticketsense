import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBaseDocument


PII_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\s-]?){9,14}(?!\d)"),
    "secret": re.compile(r"(?i)\b(?:api[_ -]?key|password|token)\s*[:=]\s*\S+"),
}

DEPARTMENTS = {
    "Networking": ("vpn", "wifi", "network", "dns", "firewall", "latency", "proxy"),
    "Cloud Infrastructure": ("aws", "cloud", "ec2", "s3", "instance", "storage", "iam"),
    "SAP": ("sap", "tcode", "idoc", "purchase order", "st22", "sp01"),
    "Human Resources": ("payroll", "leave", "benefit", "timesheet", "onboarding", "hr"),
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def redact(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    clean = text
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(clean):
            found.append(label)
            clean = pattern.sub(f"[{label.upper()} REDACTED]", clean)
    return clean, found


async def analyze_ticket(db: AsyncSession, subject: str, description: str, department_id=None) -> dict:
    raw = f"{subject} {description}"
    clean, pii = redact(raw)
    lowered = clean.lower()
    dept_scores = {name: sum(term in lowered for term in terms) for name, terms in DEPARTMENTS.items()}
    category = max(dept_scores, key=dept_scores.get) if max(dept_scores.values()) else "Service Desk"
    urgent_terms = ("outage", "production", "all users", "security", "breach", "down", "critical")
    high_terms = ("blocked", "cannot", "failed", "error", "urgent")
    impact = sum(term in lowered for term in urgent_terms)
    priority = "urgent" if impact >= 2 else "high" if any(x in lowered for x in high_terms) else "medium"
    sentiment = "negative" if any(x in lowered for x in ("frustrated", "unacceptable", "angry", "still not")) else "neutral"

    query = select(KnowledgeBaseDocument)
    if department_id:
        query = query.where(KnowledgeBaseDocument.department_id == department_id)
    docs = (await db.scalars(query.limit(80))).all()
    wanted = _tokens(clean)
    ranked = []
    for doc in docs:
        overlap = len(wanted & _tokens(f"{doc.title} {doc.content}"))
        score = min(0.98, 0.35 + overlap / max(8, len(wanted)))
        if overlap:
            ranked.append((score, doc))
    ranked.sort(key=lambda item: item[0], reverse=True)
    evidence = [
        {"title": d.title, "excerpt": d.content[:220].replace("\n", " "), "score": round(s, 2), "source": d.source_url or "Internal knowledge base"}
        for s, d in ranked[:3]
    ]
    retrieval = evidence[0]["score"] if evidence else 0.34
    agreement = 0.92 if len(evidence) >= 2 else 0.58
    safety = not (priority == "urgent" or pii)
    confidence = round(min(0.96, retrieval * .45 + agreement * .25 + .22 + (0.05 if category != "Service Desk" else 0)), 2)
    decision = "auto_resolve" if confidence >= .90 and safety else "human_review" if confidence >= .70 else "escalate"
    if priority == "urgent":
        decision = "escalate"
    draft = (
        f"We identified this as a {category.lower()} issue with {priority} priority. "
        + (f"Based on {evidence[0]['title']}, please follow the documented recovery steps and confirm the result. " if evidence else "A support specialist will review the diagnostic details. ")
        + "Sensitive details have been protected and the case will remain tracked until confirmed resolved."
    )
    return {
        "category": category, "intent": "technical_support", "sentiment": sentiment,
        "priority_score": {"medium": 54, "high": 78, "urgent": 94}[priority],
        "sla_risk": 87 if priority == "urgent" else 62 if priority == "high" else 28,
        "pii_detected": pii, "redacted_preview": clean[:300], "evidence": evidence,
        "confidence_breakdown": {"retrieval": retrieval, "evidence_agreement": agreement, "policy_match": .91, "safety": 1.0 if safety else .45},
        "confidence": confidence, "decision": decision, "decision_reason": "High-risk tickets require expert review." if priority == "urgent" else "Decision follows tenant confidence and safety thresholds.",
        "root_causes": [{"label": "Configuration or access policy mismatch", "probability": .62}, {"label": "Service availability degradation", "probability": .24}, {"label": "Unknown — diagnostics required", "probability": .14}],
        "draft": draft,
    }
