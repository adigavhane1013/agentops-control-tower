from app.database.database import SessionLocal
from app.database.models import ApprovalRequest
from app.tools.tool_gateway import execute_refund_through_gateway


def update_approval(
    approval_id: int,
    decision: str
) -> dict:
    db = SessionLocal()

    try:
        approval = db.query(ApprovalRequest).filter(
            ApprovalRequest.id == approval_id
        ).first()

        if not approval:
            return {
                "success": False,
                "error": "Approval request not found"
            }

        if approval.status != "pending":
            return {
                "success": False,
                "error": f"Approval request is already {approval.status}"
            }

        if decision not in ["approved", "rejected"]:
            return {
                "success": False,
                "error": "Decision must be approved or rejected"
            }

        approval.status = decision

        if decision == "approved":
            refund_result = execute_refund_through_gateway(
                customer_id=approval.customer_id,
                order_id=approval.order_id,
                amount=approval.amount,
                reason=approval.reason
            )

            if not refund_result["success"]:
                db.rollback()

                return {
                    "success": False,
                    "error": "Refund execution failed",
                    "details": refund_result
                }

            db.commit()

            return {
                "success": True,
                "approval_id": approval.id,
                "status": approval.status,
                "refund": refund_result
            }

        db.commit()
        db.refresh(approval)

        return {
            "success": True,
            "approval_id": approval.id,
            "status": approval.status
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close()