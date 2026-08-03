"""
Script to update invoice_items where note contains "Tiền quỹ tháng" to item_type = 'FUND'.
Usage:
    backend/.venv/bin/python backend/scripts/update_invoice_items_fund.py          # Dry run
    backend/.venv/bin/python backend/scripts/update_invoice_items_fund.py --commit # Apply changes
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine


def main():
    commit_mode = "--commit" in sys.argv

    with Session(engine) as session:
        # Count records matching
        count_query = text(
            "SELECT COUNT(*) FROM invoice_items WHERE note ILIKE :pattern AND item_type != 'FUND'"
        )
        to_update_count = (
            session.execute(count_query, {"pattern": "%Tiền quỹ tháng%"}).scalar() or 0
        )

        # Fetch matching records details
        select_query = text(
            "SELECT id, note, item_type FROM invoice_items WHERE note ILIKE :pattern"
        )
        rows = session.execute(select_query, {"pattern": "%Tiền quỹ tháng%"}).fetchall()

        print(
            f"Found {len(rows)} total invoice_item(s) with note containing 'Tiền quỹ tháng'."
        )
        print(
            f"Number of items needing update (item_type != 'FUND'): {to_update_count}\n"
        )

        for row in rows:
            is_need = "WILL UPDATE" if row.item_type != "FUND" else "ALREADY FUND"
            print(
                f" [{is_need}] ID: {row.id} | Note: '{row.note}' | Current Type: '{row.item_type}'"
            )

        if to_update_count == 0:
            print("\nAll matching items are already set to 'FUND'. No changes needed.")
            return

        if not commit_mode:
            print(
                "\n[DRY RUN] Run the script with '--commit' to apply changes to the database."
            )
            return

        print("\nUpdating records...")
        update_query = text(
            "UPDATE invoice_items SET item_type = 'FUND' WHERE note ILIKE :pattern AND item_type != 'FUND'"
        )
        result = session.execute(update_query, {"pattern": "%Tiền quỹ tháng%"})
        session.commit()

        print(
            f"Successfully updated {result.rowcount} record(s) to item_type = 'FUND'."
        )


if __name__ == "__main__":
    main()
