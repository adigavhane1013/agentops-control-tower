from app.control_tower.control_tower import evaluate_refund_request


def test_allow_refund():
    result = evaluate_refund_request(
        customer_id=101,
        order_id=1001,
        refund_amount=5000,
        order_amount=5000,
        reason="Wrong product",
    )

    assert result["decision"] == "ALLOW"
    assert result["policy_decision"] == "ALLOW"
    assert result["risk"]["risk_level"] == "LOW"
    assert result["execution"]["success"] is True
    assert result["execution"]["status"] == "processed"


def test_human_approval_refund():
    result = evaluate_refund_request(
        customer_id=101,
        order_id=1001,
        refund_amount=10000,
        order_amount=15000,
        reason="Customer requested refund",
    )

    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["policy_decision"] == "HUMAN_APPROVAL"
    assert result["risk"]["risk_level"] == "LOW"
    assert result["execution"]["executed"] is False
    assert result["execution"]["status"] == "awaiting_human_approval"
    assert result["approval"]["success"] is True
    assert result["approval"]["status"] == "pending"


def test_block_high_risk_refund():
    result = evaluate_refund_request(
        customer_id=101,
        order_id=1001,
        refund_amount=25000,
        order_amount=30000,
        reason="Large refund request",
    )

    assert result["decision"] == "BLOCK"
    assert result["policy_decision"] == "BLOCK"
    assert result["risk"]["risk_level"] == "HIGH"
    assert result["execution"]["executed"] is False
    assert result["execution"]["status"] == "blocked"