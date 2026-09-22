from app.database.database import SessionLocal
from app.database.models import RefundRequest
from app.tools.approval_tool import create_approval_request


def create_refund_request(status="awaiting_approval"):
    db = SessionLocal()

    try:
        refund_request = RefundRequest(
            customer_id=101,
            order_id=1001,
            requested_amount=4000,
            reason="Customer requested refund",
            status=status,
        )

        db.add(refund_request)
        db.commit()
        db.refresh(refund_request)

        return refund_request.id

    finally:
        db.close()


def test_create_approval_request():
    refund_request_id = create_refund_request()

    result = create_approval_request(
        refund_request_id=refund_request_id
    )

    assert result["success"] is True
    assert result["refund_request_id"] == refund_request_id
    assert result["customer_id"] == 101
    assert result["order_id"] == 1001
    assert result["amount"] == 4000
    assert result["reason"] == "Customer requested refund"
    assert result["status"] == "pending"
    assert result["idempotent"] is False


def test_duplicate_pending_approval_is_idempotent():
    refund_request_id = create_refund_request()

    first = create_approval_request(
        refund_request_id=refund_request_id
    )

    second = create_approval_request(
        refund_request_id=refund_request_id
    )

    assert first["success"] is True
    assert first["idempotent"] is False

    assert second["success"] is True
    assert second["idempotent"] is True
    assert second["approval_id"] == first["approval_id"]


def test_approval_requires_awaiting_status():
    refund_request_id = create_refund_request(
        status="pending"
    )

    result = create_approval_request(
        refund_request_id=refund_request_id
    )

    assert result["success"] is False
    assert result["error"] == (
        "Refund request is not awaiting human approval"
    )