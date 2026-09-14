# KPI Dictionary — Supply Chain Dashboard

Version: 1.0  
Dataset: DataCo Smart Supply Chain  
Reporting basis: Order date

## Purpose

Provide leadership with a consistent overview of orders, delivery performance, order value, customers, and products. Each KPI appears as a dashboard row. Time periods appear as columns, controlled by the selected Day, Week, Month, Quarter, or Year view.

When leadership asks why a KPI changed, the LLM uses the same KPI definition, reporting period, comparison period, and filters to investigate contributing factors.

## Reporting rules

- Use `order date (DateOrders)` as the date basis for every KPI. A period represents the group of orders placed in that period.
- Count orders using distinct `Order Id`. The raw dataset contains one row per `Order Item Id`, so row counts are not order counts.
- Sum quantities and financial values at the order-item level. When building an order-level table, aggregate these values across all items in each order.
- Validate that order-level attributes are consistent across items before retaining one row per order.
- Use the same population and filters for a metric's numerator and denominator.
- Display `N/A` when the denominator is zero. Do not replace an unavailable rate or average with zero.
- Recalculate rates, averages, and distinct counts for the selected period. Do not average daily percentages or sum daily distinct customer/product counts to produce monthly values.
- Targets and performance thresholds are not yet defined. Do not infer targets from the dataset average.

## Time views

| Field | Definition | Example |
|---|---|---|
| `day_view` | Calendar date | `D2017-04-15` |
| `week_view` | ISO week-year and ISO week number; Monday start | `W2017-15` |
| `month_view` | Calendar year and month | `M2017-04` |
| `quarter_view` | Calendar year and quarter | `2017-Q2` |
| `year_view` | Calendar year, January through December | `Y2017` |

An ISO week-year can differ from the calendar year near year boundaries. Use the ISO year with the ISO week number. Do not apply a timezone shift: the source timezone has not been verified.

The date range selects which orders to include; the time view selects how to group them. For example, a four-week range can be displayed by day or by week. Label partial periods and compare equivalent time windows. The source contains order dates from January 2015 through January 2018; 2018 is not a complete reporting year.

## 1. Orders

Population: all orders placed in the selected period, including canceled orders.

| ID | Dashboard KPI | Definition / formula | Source fields | Unit |
|---|---|---|---|---|
| O01 | Total Orders | Distinct order count | `Order Id` | Orders |
| O02 | Total Order Items | Distinct order-item count | `Order Item Id` | Order lines |
| O03 | Total Quantity Ordered | Sum of item quantity | `Order Item Quantity` | Units |
| O04 | Canceled Orders | Distinct orders where order status is `CANCELED` | `Order Id`, `Order Status` | Orders |
| O05 | Order Cancellation Rate | O04 / O01 × 100 | O04, O01 | % |
| O06 | Orders by Status | Distinct orders for each source order status | `Order Id`, `Order Status` | Orders |

O06 is an expandable breakdown: `COMPLETE`, `CLOSED`, `PENDING`, `PENDING_PAYMENT`, `PROCESSING`, `ON_HOLD`, `PAYMENT_REVIEW`, `CANCELED`, and `SUSPECTED_FRAUD`. Preserve these source categories. Do not automatically interpret them as delivered, in transit, or the status known on the reporting date.

## 2. Delivery

Delivery population: orders placed in the selected period, excluding `Delivery Status = Shipping canceled`, with valid delivery status, actual shipping days, and scheduled shipping days. Missing or invalid required fields must be reported as data-quality issues rather than silently classified as late or on time.

| ID | Dashboard KPI | Definition / formula | Source fields | Unit |
|---|---|---|---|---|
| D01 | Shipping-Canceled Orders | Distinct orders with `Shipping canceled` | `Order Id`, `Delivery Status` | Orders |
| D02 | Delivery-Eligible Orders | Distinct orders in the delivery population | `Order Id`, delivery fields | Orders |
| D03 | Early Orders | Eligible orders with `Advance shipping` | `Order Id`, `Delivery Status` | Orders |
| D04 | On-Time Orders — Exact | Eligible orders with `Shipping on time` | `Order Id`, `Delivery Status` | Orders |
| D05 | Late Orders | Eligible orders with `Late delivery` | `Order Id`, `Delivery Status` | Orders |
| D06 | On-Time Delivery Rate — Including Early | (D03 + D04) / D02 × 100 | D03, D04, D02 | % |
| D07 | Late Delivery Rate | D05 / D02 × 100 | D05, D02 | % |
| D08 | Average Actual Shipping Days | Mean actual shipping days across eligible orders, counting each order once | `Days for shipping (real)` | Days |
| D09 | Average Delay of Late Orders | Mean actual minus scheduled shipping days, only across eligible late orders | `Days for shipping (real)`, `Days for shipment (scheduled)` | Days |

Derived field: `delay_days = actual_shipping_days - scheduled_shipping_days`. Negative means earlier than scheduled; zero means exactly on schedule; positive means later than scheduled.

Use the source delivery label for classification and validate it against the duration comparison for non-shipping-canceled orders. `Late_delivery_risk` is a binary outcome label, not a predicted probability.

Order cancellation (O04) and shipping cancellation (D01) are separate definitions. They can overlap; do not add them to calculate a combined canceled-order count. The delivery exclusion is based on `Delivery Status`, not an assumed equivalence with `Order Status`.

### Required dashboard note

> Delivery KPIs show the outcomes recorded in the dataset for orders placed in the selected period. They do not represent the delivery status known at that historical reporting date.

This limitation applies to all time views, not only Day view. DataCo provides recorded outcome labels but no reliable historical status snapshots or separately confirmed customer-receipt timestamp. Do not infer how many orders were still in transit at the time, simulate incomplete outcomes, or calculate an outcome-completeness rate from unverified statuses.

The description file defines shipping date as the shipment timestamp. It is not confirmed as the time the customer received the order. These metrics therefore describe the dataset's delivery classifications, not independently verified customer-delivery SLA compliance. This limitation is accepted for the current project scope.

## 3. Order Value & Profit

Population: all items belonging to orders placed in the selected period, including canceled orders. These metrics describe values recorded against orders, not cash collected or recognized accounting revenue. Do not label them as realized revenue.

| ID | Dashboard KPI | Definition / formula | Source fields | Unit |
|---|---|---|---|---|
| F01 | Order Value Before Discounts | Sum item sales before discounts | `Sales` | Currency units* |
| F02 | Total Discounts | Sum item discount amounts | `Order Item Discount` | Currency units* |
| F03 | Order Value After Discounts | Sum item totals after discounts | `Order Item Total` | Currency units* |
| F04 | Average Order Value | F03 / O01 | F03, O01 | Currency units*/order |
| F05 | Recorded Profit — Source Basis | Sum the selected profit field at item grain | `Order Profit Per Order` | Currency units* |
| F06 | Recorded Profit Margin — Source Basis | F05 / F03 × 100 | F05, F03 | % |

\* Currency has not been verified. Do not assign a USD symbol or convert currencies without source confirmation.

Audit checks support `Sales = quantity × unit price` and `Order Item Total = Sales − discount`, within a 0.011 rounding tolerance. Despite their names, item totals must be summed across the order's lines before calculating order values.

`Benefit per order` and `Order Profit Per Order` contain identical values in the audited file. Use only the selected column, never both. Profit aggregation remains a documented source-based assumption because the provided description does not fully establish financial grain or accounting treatment; F05 and F06 are provisional financial interpretations.

If a dashboard filter excludes canceled orders, apply it consistently to financial totals and the order count used for F04.

## 4. Customers & Products

Population: all orders placed in the selected period, including canceled orders.

| ID | Dashboard KPI | Definition / formula | Source fields | Unit |
|---|---|---|---|---|
| C01 | Customers with Orders | Distinct customers placing orders in the period | `Order Customer Id` | Customers |
| P01 | Products with Orders | Distinct product codes appearing in orders in the period | `Product Card Id` | Product codes |
| P02 | Average Units per Order | O03 / O01 | O03, O01 | Units/order |

C01 is not a new-customer count. P01 is not quantity sold or inventory availability. Count by product ID, not product name.

## 5. Analytical dimensions and LLM behavior

Supported investigation dimensions: Shipping Mode, Market, Order Region, Order Country, Category, and Customer Segment. Group categories by ID and name because different category IDs can share a name.

For a category breakdown, count distinct orders containing that category and aggregate only that category's item values. One order can appear in several category groups, so category order counts are not additive. Overall order KPIs with a category filter select matching orders and retain their full-order values; clearly label this behavior.

The LLM must preserve the selected KPI definition, period, comparison period, and filters. It should distinguish changes within a group from changes in the mix of orders across groups. Present counts and denominators alongside rates. Describe observed contributing factors separately from unverified operational causes, and state when the dataset cannot establish a cause.

## 6. Validation baseline

Full audited dataset, with no date or dimension filters:

| Check | Expected value |
|---|---:|
| Total orders | 65,752 |
| Total order items | 180,519 |
| Shipping-canceled orders | 2,855 |
| Delivery-eligible orders | 62,897 |
| Early orders | 15,127 |
| Exactly on-time orders | 11,722 |
| Late orders | 36,048 |
| On-time rate including early | 42.69% |
| Late rate | 57.31% |
| Average delay of late orders | 1.62 days, rounded |

Reconcile D03 + D04 + D05 to D02. D06 + D07 should equal 100% before display rounding. Validate unique item keys, consistent order attributes, and reconciliation of item-level financial sums with order-level totals.

## 7. Out of scope with current data

Do not present stock levels, stockout rates, supplier performance, shipping costs, confirmed customer-receipt times, or historical open-overdue counts as measured KPIs from this dataset. Additional source data would be needed. No additional or simulated data is required for the current dashboard scope.
