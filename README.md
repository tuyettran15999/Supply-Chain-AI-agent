# Supply Chain AI Agent — Orders KPI Demo

An order-analytics prototype built on the DataCo Smart Supply Chain dataset. A
SQLite reporting table powers both a Power BI Orders KPI view and a command-line
AI assistant. The assistant uses OpenAI function calling to choose a read-only
analytics function, then explains the returned numbers.

## What the demo does

- Reports order count, order-item count, quantity, canceled orders, and
  cancellation rate by day, ISO week, month, quarter, or year.
- Ranks historical months by cancellation rate (for months with at least 100
  orders).
- Breaks down a month's cancellations by order region, counting each order once.
- Distinguishes an observed pattern from an established cause. Regional rates
  do not reveal why individual orders were canceled.

Example questions:

```text
How did orders perform in Y2017?
Compare order performance between Y2016 and Y2017.
Which three months had the highest order cancellation rates?
Which region had the most canceled orders in May 2016?
Why was the cancellation rate high in May 2016?
```

## Reproduce locally

Use Python 3.10+ and SQLite 3.46+ (the KPI SQL uses SQLite's ISO week
formatters). Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python src/prepare_data.py
python src/build_orders_kpi.py
```

The source CSV is at `data/raw/DataCoSupplyChainDataset.csv`. The first script
creates the local, ignored `data/processed/supply_chain.db`; the second rebuilds
its `orders_kpi` table from the prepared order and item tables. Set your API key
as an environment variable before starting the assistant:

```bash
export OPENAI_API_KEY="your-api-key"
python src/agent.py
```

Type a question at the `You:` prompt, or `exit` to stop. Keep the key out of
source files and commits. OpenAI API requests may incur charges.

## How the data flows

```text
DataCo CSV → prepare_data.py → SQLite orders + order_items
                                   ↓
                          build_orders_kpi.py → orders_kpi
                                   ↓                 ↓
                            analytics tools       Power BI
                                   ↓
                              CLI agent
```

`orders` contains one row per order; `order_items` contains one row per order
item. Cancellation means `order_status = 'CANCELED'`. The reporting period is
based on order date. Rates are calculated from order counts within each period,
not averaged across smaller periods. The full dataset contains 65,752 distinct
orders, 180,519 order items, and 1,367 canceled orders.

The Power BI report is a separate prototype built from an `orders_kpi` CSV
export. This repository does not include a Power BI report file or a live
Power BI connection; the CLI agent queries the local SQLite database.

## Validation and limits

The manual question-and-answer checks are in
[`tests/agent_eval_cases.md`](tests/agent_eval_cases.md). They include the
important difference between *most canceled orders* (West of USA, 13) and
*highest cancellation rate* (South of USA, 3.88%) in May 2016.

The source ends in January 2018, so `Y2018` is a partial year. These are
historical recorded outcomes, not live order statuses. The demo cannot identify
operational root causes from the available KPI and region fields. The current
agent handles the tool calls returned in its first model response; it is a
small prototype rather than a production service.

See [`KPI_DICTIONARY.md`](KPI_DICTIONARY.md) for metric definitions and wider
dashboard scope. Only the Orders KPI workflow is implemented in this demo.
