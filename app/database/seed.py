from .database import engine, Base, SessionLocal
from .models import Customer, Order, Refund, ApprovalRequest


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if not db.query(Customer).first():
        customers = [
            Customer(
                id=101,
                name="Rahul Sharma",
                email="rahul@example.com",
                status="active"
            ),
            Customer(
                id=102,
                name="Priya Patel",
                email="priya@example.com",
                status="active"
            ),
            Customer(
                id=103,
                name="Amit Kumar",
                email="amit@example.com",
                status="active"
            ),
        ]

        orders = [
            Order(
                id=1001,
                customer_id=101,
                amount=5000,
                status="delivered"
            ),
            Order(
                id=1002,
                customer_id=102,
                amount=25000,
                status="delivered"
            ),
            Order(
                id=1003,
                customer_id=103,
                amount=3000,
                status="delivered"
            ),
        ]

        db.add_all(customers)
        db.add_all(orders)
        db.commit()

        print("Database seeded successfully.")
    else:
        print("Database already contains data. Skipping seed.")

    db.close()


if __name__ == "__main__":
    seed_database()