from app.control_tower.control_tower import evaluate_refund_request


result = evaluate_refund_request(
    customer_id=101,
    order_id=1001,
    refund_amount=5000,
    order_amount=5000,
    reason="Wrong product"
)

print(result)