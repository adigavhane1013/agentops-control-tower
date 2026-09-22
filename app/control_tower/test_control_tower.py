from app.control_tower.control_tower import evaluate_refund_request
from app.database.database import SessionLocal
from app.database.models import RefundRequest


db = SessionLocal()

try:
    refund_request = RefundRequest(
        customer_id=101,
        order_id=1001,
        requested_amount=5000,
        reason="Wrong product",
        status="pending",
    )

    db.add(refund_request)
    db.commit()
    db.refresh(refund_request)

    result = evaluate_refund_request(
        refund_request_id=refund_request.id
    )

    print(result)

finally:
    db.close()