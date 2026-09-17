from fastapi import APIRouter

from app.database.database import SessionLocal
from app.database.models import AuditLog


router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)


@router.get("/logs")
def get_audit_logs():

    db = SessionLocal()

    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .all()
        )

        return [
            {
                "id": log.id,
                "customer_id": log.customer_id,
                "order_id": log.order_id,
                "refund_amount": log.refund_amount,
                "decision": log.decision,
                "reason": log.reason
            }
            for log in logs
        ]

    finally:
        db.close()