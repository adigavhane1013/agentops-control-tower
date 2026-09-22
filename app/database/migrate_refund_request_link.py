from sqlalchemy import inspect, text

from app.database.database import engine


TABLE_NAME = "refunds"
COLUMN_NAME = "refund_request_id"
INDEX_NAME = "ux_refunds_refund_request_id"


def migrate_refund_request_link():
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if TABLE_NAME not in tables:
        raise RuntimeError(
            f"Expected table '{TABLE_NAME}' was not found."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns(TABLE_NAME)
    }

    if COLUMN_NAME in columns:
        raise RuntimeError(
            f"Migration already appears to have run: "
            f"'{COLUMN_NAME}' already exists in '{TABLE_NAME}'."
        )

    expected_columns = {
        "id",
        "customer_id",
        "order_id",
        "amount",
        "status",
        "reason",
    }

    if columns != expected_columns:
        raise RuntimeError(
            "Unexpected refunds schema.\n"
            f"Expected: {sorted(expected_columns)}\n"
            f"Found:    {sorted(columns)}"
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE refunds
                ADD COLUMN refund_request_id INTEGER
                REFERENCES refund_requests(id)
                """
            )
        )

        connection.execute(
            text(
                f"""
                CREATE UNIQUE INDEX {INDEX_NAME}
                ON refunds(refund_request_id)
                """
            )
        )

    print("Refund request link migration completed successfully.")


if __name__ == "__main__":
    migrate_refund_request_link()