from sqlalchemy import inspect, text

from app.database.database import engine, Base
from app.database.models import ApprovalRequest


LEGACY_TABLE = "approval_requests_legacy"
CURRENT_TABLE = "approval_requests"


def migrate_approval_requests():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if LEGACY_TABLE in tables:
        raise RuntimeError(
            f"Migration already appears to have run: "
            f"'{LEGACY_TABLE}' already exists."
        )

    if CURRENT_TABLE not in tables:
        raise RuntimeError(
            f"Expected existing table '{CURRENT_TABLE}' was not found."
        )

    current_columns = {
        column["name"]
        for column in inspector.get_columns(CURRENT_TABLE)
    }

    expected_legacy_columns = {
        "id",
        "customer_id",
        "order_id",
        "amount",
        "reason",
        "status",
    }

    if current_columns != expected_legacy_columns:
        raise RuntimeError(
            "Unexpected approval_requests schema.\n"
            f"Expected: {sorted(expected_legacy_columns)}\n"
            f"Found:    {sorted(current_columns)}"
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                f"ALTER TABLE {CURRENT_TABLE} "
                f"RENAME TO {LEGACY_TABLE}"
            )
        )

        # Create the new approval_requests table from the updated
        # SQLAlchemy model. The old table has already been renamed,
        # so create_all() can safely create the new schema.
        Base.metadata.create_all(bind=engine)

    print("Approval request migration completed successfully.")


if __name__ == "__main__":
    migrate_approval_requests()