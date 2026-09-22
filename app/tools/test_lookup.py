from app.tools.lookup_tool import get_customer_order


def test_get_customer_order():
    result = get_customer_order(101, 1001)

    assert result["success"] is True
    assert result["customer"]["id"] == 101
    assert result["order"]["id"] == 1001


def test_get_customer_order_rejects_wrong_customer_order_pair():
    result = get_customer_order(101, 1002)

    assert result["success"] is False
    assert result["error"] == "Order not found for this customer"