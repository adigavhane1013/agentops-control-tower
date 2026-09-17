from .database import SessionLocal
from .models import Customer, Order


def test_database():
    db = SessionLocal()

    customer = db.query(Customer).filter(Customer.id == 101).first()
    order = db.query(Order).filter(Order.customer_id == 101).first()

    print("Customer:")
    print(f"ID: {customer.id}")
    print(f"Name: {customer.name}")
    print(f"Email: {customer.email}")
    print(f"Status: {customer.status}")

    print("\nOrder:")
    print(f"ID: {order.id}")
    print(f"Customer ID: {order.customer_id}")
    print(f"Amount: ₹{order.amount}")
    print(f"Status: {order.status}")

    db.close()


if __name__ == "__main__":
    test_database()