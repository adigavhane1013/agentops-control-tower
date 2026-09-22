from app.tools.refund_request_tool import create_canonical_refund_request


def test_create_canonical_refund_request():
    result = create_canonical_refund_request(
        customer_id=101,
        order_id=1001,
        requested_amount=4000,
        reason="Wrong product",
    )

    assert result["success"] is True
    assert result["refund_request_id"] is not None
    assert result["customer_id"] == 101
    assert result["order_id"] == 1001
    assert result["requested_amount"] == 4000
    assert result["status"] == "pending"


def test_rejects_wrong_customer_order_pair():
    result = create_canonical_refund_request(
        customer_id=101,
        order_id=1002,
        requested_amount=4000,
        reason="Wrong product",
    )

    assert result["success"] is False
    assert result["error"] == "Order not found for this customer"


def test_rejects_non_positive_amount():
    result = create_canonical_refund_request(
        customer_id=101,
        order_id=1001,
        requested_amount=0,
        reason="Invalid amount",
    )

    assert result["success"] is False
    assert result["error"] == "Refund amount must be greater than zero"