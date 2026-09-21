import sqlite3
from pathlib import Path
from datetime import datetime


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_DIR / "data" / "processed" / "supply_chain.db"


def get_order_kpis(time_grain: str, time_stamp: str) -> dict:
    query = """
        SELECT
            time_stamp,
            time_grain,
            total_orders,
            total_order_items,
            total_quantity_ordered,
            canceled_orders,
            cancellation_rate_pct
        FROM orders_kpi
        WHERE time_grain = ?
          AND time_stamp = ?
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        result = connection.execute(
            query,
            (time_grain, time_stamp),
        ).fetchone()

    if result is None:
        return {
            "status": "not_found",
            "time_grain": time_grain,
            "time_stamp": time_stamp,
        }

    return {
        "status": "success",
        **dict(result),
    }

def get_problem_periods(limit: int = 5) -> list[dict]:
    query = """
        SELECT
            time_stamp,
            total_orders,
            canceled_orders,
            cancellation_rate_pct
        FROM orders_kpi
        WHERE time_grain = 'month'
          AND total_orders >= 100
        ORDER BY cancellation_rate_pct DESC, canceled_orders DESC
        LIMIT ?
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, (limit,)).fetchall()

    return [dict(row) for row in rows]

def get_cancellations_by_region(time_stamp: str) -> list[dict]:
    month = datetime.strptime(time_stamp, "M%Y-%m")
    start_date = month.strftime("%Y-%m-01")

    if month.month == 12:
        end_date = f"{month.year + 1}-01-01"
    else:
        end_date = f"{month.year}-{month.month + 1:02d}-01"

    query = """
        WITH monthly_orders AS (
            SELECT DISTINCT
                order_id,
                order_region,
                order_status
            FROM order_items
            WHERE order_datetime >= ?
              AND order_datetime < ?
        )
        SELECT
            order_region,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END)
                AS canceled_orders,
            ROUND(
                100.0 * SUM(CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS cancellation_rate_pct
        FROM monthly_orders
        GROUP BY order_region
        ORDER BY cancellation_rate_pct DESC, canceled_orders DESC
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, (start_date, end_date)).fetchall()

    return [dict(row) for row in rows]

if __name__ == "__main__":
    kpis = get_order_kpis(
        time_grain="year",
        time_stamp="Y2018",
    )
    print(kpis)
    print(get_problem_periods())
    print(get_cancellations_by_region("M2016-05"))