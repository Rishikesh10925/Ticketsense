from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def analytics(user: User = Depends(require_role("support_agent", "manager", "enterprise_admin", "ai_admin", "department_engineer", "admin")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Ticket.status, func.count()).where(Ticket.tenant_id == user.tenant_id).group_by(Ticket.status))).all()
    counts = dict(rows); total = sum(counts.values())
    avg = await db.scalar(select(func.avg(Ticket.confidence_score)).where(Ticket.tenant_id == user.tenant_id))
    return {"total_tickets": total, "open_tickets": counts.get("open", 0) + counts.get("in_review", 0),
        "resolved_tickets": counts.get("resolved", 0), "escalated_tickets": counts.get("escalated", 0),
        "average_confidence": round(float(avg or 0), 2), "status_distribution": counts}
