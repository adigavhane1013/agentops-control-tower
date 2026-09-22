from app.database.database import SessionLocal
from app.database.models import Refund, RefundRequest
from app.tools.refund_tool import execute_refund


def create_refund_request(status="approved"):
    db = SessionLocal()

    try:
        refund_request = RefundRequest(
            customer_id=101,
            order_id=1001,
            requested_amount=4000,
            reason="Wrong product",
            status=status,
        )

        db.add(refund_request)
        db.commit()
        db.refresh(refund_request)

        return refund_request.id

    finally:
        db.close()


def test_execute_refund():
    refund_request_id = create_refund_request(
        status="approved"
    )

    result = execute_refund(
        refund_request_id=refund_request_id
    )

    assert result["success"] is True
    assert result["refund_request_id"] == refund_request_id
    assert result["customer_id"] == 101
    assert result["order_id"] == 1001
    assert result["amount"] == 4000
    assert result["status"] == "processed"
    assert result["reason"] == "Wrong product"
    assert result["idempotent"] is False

    db = SessionLocal()

    try:
        refund_request = (
            db.query(RefundRequest)
            .filter(RefundRequest.id == refund_request_id)
            .first()
        )

        assert refund_request.status == "processed"

    finally:
        db.close()


def test_pending_request_cannot_execute():
    refund_request_id = create_refund_request(
        status="pending"
    )

    result = execute_refund(
        refund_request_id=refund_request_id
    )

    assert result["success"] is False
    assert result["error"] == (
        "Refund request is not approved for execution"
    )


def test_duplicate_execution_is_idempotent():
    refund_request_id = create_refund_request(
        status="approved"
    )

    first = execute_refund(
        refund_request_id=refund_request_id
    )

    second = execute_refund(
        refund_request_id=refund_request_id
    )

    assert first["success"] is True
    assert first["idempotent"] is False

    assert second["success"] is True
    assert second["idempotent"] is True
    assert second["refund_id"] == first["refund_id"]