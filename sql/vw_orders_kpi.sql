CREATE TABLE orders_kpi AS
WITH daily_orders AS (
    SELECT
        strftime('D%Y-%m-%d', order_datetime) AS time_stamp,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END) AS canceled_orders
    FROM orders
    GROUP BY strftime('D%Y-%m-%d', order_datetime)
),

daily_items AS (
    SELECT
        strftime('D%Y-%m-%d', order_datetime) AS time_stamp,
        COUNT(*) AS total_order_items,
        SUM(order_item_quantity) AS total_quantity_ordered
    FROM order_items
    GROUP BY strftime('D%Y-%m-%d', order_datetime)
),

weekly_orders AS (
    SELECT
        strftime('W%G-%V', order_datetime) AS time_stamp,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END) AS canceled_orders
    FROM orders
    GROUP BY strftime('W%G-%V', order_datetime)
),

weekly_items AS (
    SELECT
        strftime('W%G-%V', order_datetime) AS time_stamp,
        COUNT(*) AS total_order_items,
        SUM(order_item_quantity) AS total_quantity_ordered
    FROM order_items
    GROUP BY strftime('W%G-%V', order_datetime)
),

monthly_orders AS
(SELECT
    strftime('M%Y-%m', order_datetime) AS time_stamp,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END) AS canceled_orders
FROM orders
GROUP BY strftime('M%Y-%m', order_datetime)
),

monthly_items AS
(SELECT
    strftime('M%Y-%m', order_datetime) AS time_stamp,
    COUNT(*) AS total_order_items,
    SUM(order_item_quantity) AS total_quantity_ordered
FROM order_items
GROUP BY strftime('M%Y-%m', order_datetime)
),

quarterly_orders AS (
    SELECT
        strftime('%Y', order_datetime) || '-Q' ||
        (
            (CAST(strftime('%m', order_datetime) AS INTEGER) - 1) / 3 + 1
        ) AS time_stamp,
        COUNT(*) AS total_orders,
        SUM(
            CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END
        ) AS canceled_orders
    FROM orders
    GROUP BY time_stamp
),
quarterly_items AS (
    SELECT
        strftime('%Y', order_datetime) || '-Q' ||
        (
            (CAST(strftime('%m', order_datetime) AS INTEGER) - 1) / 3 + 1
        ) AS time_stamp,
        COUNT(*) AS total_order_items,
        SUM(order_item_quantity) AS total_quantity_ordered
    FROM order_items
    GROUP BY time_stamp
),

yearly_orders AS (
    SELECT
        strftime('Y%Y', order_datetime) AS time_stamp,
        COUNT(*) AS total_orders,
        SUM(
            CASE WHEN order_status = 'CANCELED' THEN 1 ELSE 0 END
        ) AS canceled_orders
    FROM orders
    GROUP BY strftime('Y%Y', order_datetime)
),

yearly_items AS (
    SELECT
        strftime('Y%Y', order_datetime) AS time_stamp,
        COUNT(*) AS total_order_items,
        SUM(order_item_quantity) AS total_quantity_ordered
    FROM order_items
    GROUP BY strftime('Y%Y', order_datetime)
)

SELECT
    a.time_stamp,
    'day' AS time_grain,
    a.total_orders,
    b.total_order_items,
    b.total_quantity_ordered,
    a.canceled_orders,
    ROUND(100.0 * a.canceled_orders / NULLIF(a.total_orders, 0),2) AS cancellation_rate_pct
FROM daily_orders AS a
LEFT JOIN daily_items AS b ON a.time_stamp = b.time_stamp

UNION ALL
SELECT
    w.time_stamp AS time_stamp,
    'week' AS time_grain,
    w.total_orders,
    i.total_order_items,
    i.total_quantity_ordered,
    w.canceled_orders,
    ROUND(100.0 * w.canceled_orders / NULLIF(w.total_orders, 0),2) AS cancellation_rate_pct
FROM weekly_orders AS w
LEFT JOIN weekly_items AS i ON w.time_stamp = i.time_stamp

UNION ALL

SELECT
    c.time_stamp,
    'month' AS time_grain,
    c.total_orders,
    d.total_order_items,
    d.total_quantity_ordered,
    c.canceled_orders,
    ROUND(100.0 * c.canceled_orders / NULLIF(c.total_orders, 0),2) AS cancellation_rate_pct
FROM monthly_orders AS c
LEFT JOIN monthly_items AS d ON c.time_stamp = d.time_stamp

UNION ALL

SELECT
    q.time_stamp AS time_stamp,
    'quarter' AS time_grain,
    q.total_orders,
    i.total_order_items,
    i.total_quantity_ordered,
    q.canceled_orders,
    ROUND(100.0 * q.canceled_orders / NULLIF(q.total_orders, 0),2) AS cancellation_rate_pct
FROM quarterly_orders AS q
LEFT JOIN quarterly_items AS i ON q.time_stamp = i.time_stamp

UNION ALL

SELECT
    y.time_stamp AS time_stamp,
    'year' AS time_grain,
    y.total_orders,
    i.total_order_items,
    i.total_quantity_ordered,
    y.canceled_orders,
    ROUND(100.0 * y.canceled_orders / NULLIF(y.total_orders, 0),2) AS cancellation_rate_pct
FROM yearly_orders AS y
LEFT JOIN yearly_items AS i
    ON y.time_stamp = i.time_stamp
ORDER BY 2, 1;



-- SELECT
--     SUM(o.total_orders) AS total_orders,
--     SUM(i.total_order_items) AS total_order_items,
--     SUM(i.total_quantity_ordered) AS total_quantity_ordered,
--     SUM(o.canceled_orders) AS canceled_orders,
--     SUM(
--         CASE WHEN i.time_stamp IS NULL THEN 1 ELSE 0 END
--     ) AS months_without_items
-- FROM monthly_orders AS o
-- LEFT JOIN monthly_items AS i
--     ON o.time_stamp = i.time_stamp;

