from pathlib import Path
import pandas as pd

data_path = (
    Path(__file__).parent
    / "data"
    / "raw"
    / "DataCoSupplyChainDataset.csv"
)

df = pd.read_csv(data_path, encoding="latin1")

print("Shape:", df.shape)
print(df.head())

print(df["Product Card Id"].nunique())

###Table breaks down by Order Item Id - which is an unique item ID for each order
# Order ID: which order?
# Product Card Id: which product?

print(df[df["Order Id"] == 7814].to_string(index=False))

print(df["Delivery Status"].value_counts()) #Late delivery, Late delivery, Shipping on time, Shipping canceled
print(df.groupby("Delivery Status")["Order Id"].nunique())

order_counts = df.groupby("Delivery Status")["Order Id"].nunique()

late_orders = order_counts["Late delivery"]
eligible_orders = order_counts.sum() - order_counts["Shipping canceled"]

late_rate = late_orders / eligible_orders

print("Non-canceled orders:", eligible_orders)
print(f"Late delivery rate: {late_rate:.2%}")

shipping_summary = df.groupby(
    ["Shipping Mode", "Delivery Status"]
)["Order Id"].nunique().unstack(fill_value=0)

print(shipping_summary.to_string())

shipping_summary["Non-canceled orders"] = (
    shipping_summary["Advance shipping"]
    + shipping_summary["Late delivery"]
    + shipping_summary["Shipping on time"]
)

shipping_summary["Late rate (%)"] = (
    shipping_summary["Late delivery"]
    / shipping_summary["Non-canceled orders"]
    * 100
)

print(
    shipping_summary[
        ["Non-canceled orders", "Late rate (%)"]
    ].round(2).to_string()
)

first_class = df[
    (df["Shipping Mode"] == "First Class")
    & (df["Delivery Status"] != "Shipping canceled")
]

first_class_orders = first_class.drop_duplicates(subset="Order Id")

print(
    first_class_orders[
        ["Days for shipment (scheduled)", "Days for shipping (real)"]
    ].value_counts().to_string()
)

non_canceled_orders = df[
    df["Delivery Status"] != "Shipping canceled"
].drop_duplicates(subset="Order Id")

print(
    non_canceled_orders.groupby(
        [
            "Shipping Mode",
            "Days for shipment (scheduled)",
            "Days for shipping (real)"
        ]
    ).size().to_string()
)

non_canceled_orders = non_canceled_orders.copy()

non_canceled_orders["delay_days"] = (
    non_canceled_orders["Days for shipping (real)"]
    - non_canceled_orders["Days for shipment (scheduled)"]
)

print(non_canceled_orders["delay_days"].value_counts().sort_index())

late_orders = non_canceled_orders[
    non_canceled_orders["delay_days"] > 0
]

avg_delay = late_orders["delay_days"].mean()

print(f"Độ trễ trung bình của các đơn trễ: {avg_delay:.2f} ngày")

delay_by_mode = late_orders.groupby("Shipping Mode")["delay_days"].agg(
    late_order_count="count",
    avg_delay_days="mean"
)

print(delay_by_mode.round(2).to_string())

print(
    first_class_orders[
        [
            "Order Id",
            "order date (DateOrders)",
            "shipping date (DateOrders)",
            "Days for shipment (scheduled)",
            "Days for shipping (real)"
        ]
    ].head(10).to_string(index=False)
)

first_class_orders = first_class_orders.copy()

order_time = pd.to_datetime(
    first_class_orders["order date (DateOrders)"],
    format="%m/%d/%Y %H:%M"
)

shipping_time = pd.to_datetime(
    first_class_orders["shipping date (DateOrders)"],
    format="%m/%d/%Y %H:%M"
)

first_class_orders["elapsed_days"] = (
    (shipping_time - order_time).dt.total_seconds() / 86400
)

print(
    first_class_orders["elapsed_days"]
    .value_counts()
    .sort_index()
)

first_class_orders["order_year"] = order_time.dt.year

print(
    first_class_orders.groupby("order_year").agg(
        order_count=("Order Id", "nunique"),
        avg_elapsed_days=("elapsed_days", "mean")
    ).to_string()
)

non_canceled_orders["calculated_late"] = (
    non_canceled_orders["delay_days"] > 0
).astype(int)

print(
    pd.crosstab(
        non_canceled_orders["Late_delivery_risk"],
        non_canceled_orders["calculated_late"],
        rownames=["Nhãn có sẵn"],
        colnames=["Nhãn tự tính"]
    )
)