from app.tools.approval_tool import create_approval_request


def test_create_approval_request():
    result = create_approval_request(
        customer_id=101,
        order_id=1001,
        amount=10000,
        reason="Customer requested refund"
    )

    assert result["success"] is True
    assert result["customer_id"] == 101
    assert result["order_id"] == 1001
    assert result["amount"] == 10000
    assert result["status"] == "pending"