"""Rebuild the derived orders_kpi table from the prepared SQLite tables."""

import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_DIR / "data" / "processed" / "supply_chain.db"
SQL_PATH = PROJECT_DIR / "sql" / "vw_orders_kpi.sql"


def main() -> None:
    if sqlite3.sqlite_version_info < (3, 46, 0):
        raise RuntimeError(
            "SQLite 3.46+ is required for ISO week formatting; "
            f"this Python uses SQLite {sqlite3.sqlite_version}."
        )

    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Missing {DATABASE_PATH}. Run python src/prepare_data.py first."
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not {"orders", "order_items"} <= tables:
            raise RuntimeError("The database needs orders and order_items tables.")

        connection.execute("DROP TABLE IF EXISTS orders_kpi")
        connection.executescript(SQL_PATH.read_text(encoding="utf-8"))

        for grain in ("day", "week", "month", "quarter", "year"):
            totals = connection.execute(
                """SELECT SUM(total_orders), SUM(total_order_items),
                          SUM(total_quantity_ordered), SUM(canceled_orders)
                   FROM orders_kpi WHERE time_grain = ?""",
                (grain,),
            ).fetchone()
            print(f"{grain}: {totals}")
            if totals != (65752, 180519, 384079, 1367):
                raise RuntimeError(f"KPI totals did not reconcile for {grain}.")


if __name__ == "__main__":
    main()
