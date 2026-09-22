from app.database.database import SessionLocal
from app.database.models import RefundRequest
from app.tools.approval_tool import (
    create_approval_request,
    update_approval,
)


def create_refund_request():
    db = SessionLocal()

    try:
        refund_request = RefundRequest(
            customer_id=101,
            order_id=1001,
            requested_amount=4000,
            reason="Automated approval test",
            status="awaiting_approval",
        )

        db.add(refund_request)
        db.commit()
        db.refresh(refund_request)

        return refund_request.id

    finally:
        db.close()


def test_approve_refund():
    refund_request_id = create_refund_request()

    approval = create_approval_request(
        refund_request_id=refund_request_id
    )

    assert approval["success"] is True

    approval_id = approval["approval_id"]

    result = update_approval(
        approval_id=approval_id,
        decision="approved",
    )

    assert result["success"] is True
    assert result["status"] == "approved"
    assert result["refund_request_id"] == refund_request_id
    assert result["refund_status"] == "processed"
    assert result["refund"]["success"] is True
    assert result["refund"]["amount"] == 4000


def test_reject_refund():
    refund_request_id = create_refund_request()

    approval = create_approval_request(
        refund_request_id=refund_request_id
    )

    result = update_approval(
        approval_id=approval["approval_id"],
        decision="rejected",
    )

    assert result["success"] is True
    assert result["status"] == "rejected"
    assert result["refund_status"] == "rejected"