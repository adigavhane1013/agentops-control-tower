import pytest

from app.database.database import SessionLocal
from app.database.models import RefundRequest
from app.tools.tool_gateway import execute_refund_through_gateway


def create_refund_request(
    customer_id,
    order_id,
    requested_amount,
    reason,
):
    db = SessionLocal()

    try:
        refund_request = RefundRequest(
            customer_id=customer_id,
            order_id=order_id,
            requested_amount=requested_amount,
            reason=reason,
            status="pending",
        )

        db.add(refund_request)
        db.commit()
        db.refresh(refund_request)

        return refund_request.id

    finally:
        db.close()


def test_invalid_order_id():
    refund_request_id = create_refund_request(
        customer_id=102,
        order_id=0,
        requested_amount=5000,
        reason="Invalid order test",
    )

    with pytest.raises(ValueError, match="Invalid order ID"):
        execute_refund_through_gateway(
            refund_request_id=refund_request_id
        )


def test_invalid_amount():
    refund_request_id = create_refund_request(
        customer_id=102,
        order_id=1002,
        requested_amount=0,
        reason="Invalid amount test",
    )

    with pytest.raises(
        ValueError,
        match="Refund amount must be greater than zero",
    ):
        execute_refund_through_gateway(
            refund_request_id=refund_request_id
        )


def test_invalid_customer_id():
    refund_request_id = create_refund_request(
        customer_id=0,
        order_id=1002,
        requested_amount=5000,
        reason="Invalid customer test",
    )

    with pytest.raises(ValueError, match="Invalid customer ID"):
        execute_refund_through_gateway(
            refund_request_id=refund_request_id
        )