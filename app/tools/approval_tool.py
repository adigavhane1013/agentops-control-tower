from app.database.database import SessionLocal
from app.database.models import ApprovalRequest
from app.tools.refund_tool import execute_refund


def create_approval_request(
    customer_id: int,
    order_id: int,
    amount: float,
    reason: str
) -> dict:

    db = SessionLocal()

    try:
        approval = ApprovalRequest(
            customer_id=customer_id,
            order_id=order_id,
            amount=amount,
            reason=reason,
            status="pending"
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return {
            "success": True,
            "approval_id": approval.id,
            "customer_id": approval.customer_id,
            "order_id": approval.order_id,
            "amount": approval.amount,
            "reason": approval.reason,
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


def update_approval(
    approval_id: int,
    decision: str
) -> dict:

    db = SessionLocal()

    try:
        approval = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.id == approval_id)
            .first()
        )

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

        if decision == "rejected":

            approval.status = "rejected"

            db.commit()
            db.refresh(approval)

            return {
                "success": True,
                "approval_id": approval.id,
                "status": approval.status
            }

        refund_result = execute_refund(
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

        approval.status = "approved"

        db.commit()
        db.refresh(approval)

        return {
            "success": True,
            "approval_id": approval.id,
            "status": approval.status,
            "refund": refund_result
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close()