from app.database.database import SessionLocal
from app.database.models import Customer, Order


def get_customer_order(customer_id: int, order_id: int) -> dict:
    """Retrieve an exact customer and order pair from the database."""

    if customer_id <= 0:
        return {
            "success": False,
            "error": "Invalid customer ID"
        }

    if order_id <= 0:
        return {
            "success": False,
            "error": "Invalid order ID"
        }

    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "error": "Customer not found"
            }

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id,
                Order.customer_id == customer_id
            )
            .first()
        )

        if not order:
            return {
                "success": False,
                "error": "Order not found for this customer"
            }

        return {
            "success": True,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "status": customer.status
            },
            "order": {
                "id": order.id,
                "customer_id": order.customer_id,
                "amount": order.amount,
                "status": order.status
            }
        }

    finally:
        db.close()