from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_PATH = PROJECT_DIR / "data" / "raw" / "DataCoSupplyChainDataset.csv"

df = pd.read_csv(RAW_PATH, encoding = "latin1")

order_items = df.copy()

print("Raw data:", df.shape)
print("Order items:", order_items.shape)

order_items.columns = (
    order_items.columns
    .str.strip()
    .str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
    .str.strip("_")
)

print(order_items.columns.tolist())

order_items = order_items.rename(columns={
    "order_date_dateorders": "order_datetime",
    "shipping_date_dateorders": "shipping_datetime",
    "days_for_shipping_real": "actual_shipping_days",
    "days_for_shipment_scheduled": "scheduled_shipping_days"
})

for column in ["order_datetime", "shipping_datetime"]:
    order_items[column] = pd.to_datetime(
        order_items[column],
        format="%m/%d/%Y %H:%M",
        errors="raise"
    )

print(
    order_items[
        ["order_id", "order_datetime", "shipping_datetime"]
    ].head()
)

print(order_items[["order_datetime", "shipping_datetime"]].dtypes)

print("Total rows:", len(order_items))
print("Unique orders:", order_items["order_id"].nunique())

print(
    "Missing order item IDs:",
    order_items["order_item_id"].isna().sum()
)

print(
    "Duplicate order item IDs:",
    order_items["order_item_id"].duplicated().sum()
)

print(
    "Missing order IDs:",
    order_items["order_id"].isna().sum()
)
# Check consistency of order-level fields across items
order_fields = [
    "order_datetime",
    "order_status",
    "delivery_status",
    "shipping_mode",
    "actual_shipping_days",
    "scheduled_shipping_days"
]

field_counts = (
    order_items.groupby("order_id")[order_fields]
    .nunique(dropna=False)
)

conflicting_orders = field_counts.gt(1).sum()

print("Orders with conflicting values by field:")
print(conflicting_orders)

# Create one row per order using validated order-level fields
orders = (
    order_items[["order_id"] + order_fields]
    .drop_duplicates(subset="order_id")
    .copy()
)

print("Orders table shape:", orders.shape)
print("Order ID is unique:", orders["order_id"].is_unique)
print(orders.head().to_string(index=False))

import sqlite3

# Create the output directory
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = PROCESSED_DIR / "supply_chain.db"

# Save prepared tables to a local database
with sqlite3.connect(DATABASE_PATH) as connection:
    order_items.to_sql(
        "order_items",
        connection,
        if_exists="replace",
        index=False
    )

    orders.to_sql(
        "orders",
        connection,
        if_exists="replace",
        index=False
    )

    # Verify the saved orders table using SQL
    result = pd.read_sql_query(
        "SELECT COUNT(*) AS total_orders FROM orders",
        connection
    )

print(result.to_string(index=False))