from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.refunds import router
from app.database.database import SessionLocal
from app.database.models import RefundRequest as RefundRequestModel


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_refund_request_preserves_original_requested_amount():
    response = client.post(
        "/refunds/request",
        json={
            "customer_id": 101,
            "order_id": 1001,
            "refund_amount": 6000,
            "reason": "Customer requested refund",
        },
    )

    assert response.status_code == 200

    db = SessionLocal()

    try:
        refund_request = (
            db.query(RefundRequestModel)
            .order_by(RefundRequestModel.id.desc())
            .first()
        )

        assert refund_request is not None
        assert refund_request.customer_id == 101
        assert refund_request.order_id == 1001
        assert refund_request.requested_amount == 6000
        assert refund_request.reason == "Customer requested refund"
        assert refund_request.status == "blocked"

    finally:
        db.close()


def test_refund_request_amount_is_immutable():
    response = client.post(
        "/refunds/request",
        json={
            "customer_id": 101,
            "order_id": 1001,
            "refund_amount": 6000,
            "reason": "Customer requested refund",
        },
    )

    assert response.status_code == 200

    db = SessionLocal()

    try:
        refund_request = (
            db.query(RefundRequestModel)
            .order_by(RefundRequestModel.id.desc())
            .first()
        )

        assert refund_request is not None
        assert refund_request.requested_amount == 6000

        refund_request.requested_amount = 4000

        try:
            db.commit()
            assert False, "Refund request amount was modified"
        except ValueError as exc:
            assert "requested_amount" in str(exc)
            db.rollback()

        db.refresh(refund_request)

        assert refund_request.requested_amount == 6000

    finally:
        db.close()