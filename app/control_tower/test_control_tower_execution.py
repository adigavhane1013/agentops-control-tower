from app.control_tower.control_tower import evaluate_refund_request
from app.database.database import SessionLocal
from app.database.models import RefundRequest


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


def test_allow_refund():
    refund_request_id = create_refund_request(
        customer_id=101,
        order_id=1001,
        requested_amount=4000,
        reason="Wrong product",
    )

    result = evaluate_refund_request(
        refund_request_id=refund_request_id
    )

    assert result["decision"] == "ALLOW"
    assert result["policy_decision"] == "ALLOW"
    assert result["risk"]["risk_level"] == "LOW"
    assert result["execution"]["success"] is True
    assert result["execution"]["status"] == "processed"


def test_human_approval_refund():
    refund_request_id = create_refund_request(
        customer_id=102,
        order_id=1002,
        requested_amount=10000,
        reason="Customer requested refund",
    )

    result = evaluate_refund_request(
        refund_request_id=refund_request_id
    )

    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["policy_decision"] == "HUMAN_APPROVAL"
    assert result["risk"]["risk_level"] == "LOW"
    assert result["execution"]["executed"] is False
    assert result["execution"]["status"] == "awaiting_human_approval"
    assert result["approval"]["success"] is True
    assert result["approval"]["status"] == "pending"


def test_block_high_risk_refund():
    refund_request_id = create_refund_request(
        customer_id=101,
        order_id=1001,
        requested_amount=25000,
        reason="Large refund request",
    )

    result = evaluate_refund_request(
        refund_request_id=refund_request_id
    )

    assert result["decision"] == "BLOCK"
    assert result["policy_decision"] == "BLOCK"
    assert result["risk"]["risk_level"] == "HIGH"
    assert result["execution"]["executed"] is False
    assert result["execution"]["status"] == "blocked"