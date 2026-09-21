import json

from openai import OpenAI

from analytics_tools import (
    get_order_kpis,
    get_problem_periods,
    get_cancellations_by_region,
)

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "name": "get_order_kpis",
        "description": (
            "Retrieve order KPI metrics for one reporting period "
            "from the supply chain analytics database."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "time_grain": {
                    "type": "string",
                    "enum": ["day", "week", "month", "quarter", "year"],
                    "description": "Reporting time grain.",
                },
                "time_stamp": {
                    "type": "string",
                    "description": (
                        "Reporting period identifier, such as "
                        "D2018-01-31, W2018-04, M2017-12, "
                        "2018-Q1, or Y2018."
                    ),
                },
            },
            "required": ["time_grain", "time_stamp"],
            "additionalProperties": False,
        },
        "strict": True,
    },
{
    "type": "function",
    "name": "get_problem_periods",
    "description": (
        "Return the months with the highest order cancellation rates "
        "in the historical dataset. This ranks periods; it does not "
        "identify root causes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of months to return, from 1 to 10.",
            },
        },
        "required": ["limit"],
        "additionalProperties": False,
    },
    "strict": True,
},
{
    "type": "function",
    "name": "get_cancellations_by_region",
    "description": (
        "Break down order counts and cancellation rates by order region "
        "for one month. This shows where cancellations occurred, "
        "but does not establish their cause."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "time_stamp": {
                "type": "string",
                "description": "Month identifier in MYYYY-MM format, such as M2016-05.",
            },
        },
        "required": ["time_stamp"],
        "additionalProperties": False,
    },
    "strict": True,
}
]


def run_agent(user_question: str) -> str:
    input_messages = [
        {
            "role": "user",
            "content": user_question,
        }
    ]

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You are a supply chain analytics assistant. "
            "Use the available tool when the user asks about order KPIs. "
            "Base your answer only on the tool result. "
            "Clearly state the reporting period."
        ),
        tools=TOOLS,
        input=input_messages,
    )

    input_messages += response.output

    tool_was_called = False
    region_result = None

    for item in response.output:
        if item.type != "function_call":
            continue

        tool_was_called = True
        arguments = json.loads(item.arguments)

        print(f"Tool selected: {item.name}")
        print(f"Tool arguments: {arguments}")

        if item.name == "get_order_kpis":
            tool_result = get_order_kpis(**arguments)
        elif item.name == "get_problem_periods":
            tool_result = get_problem_periods(**arguments)
        elif item.name == "get_cancellations_by_region":
            tool_result = get_cancellations_by_region(**arguments)
            region_result = tool_result
        else:
            raise ValueError(f"Unknown tool: {item.name}")

        print(f"Tool result: {tool_result}")

        input_messages.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(tool_result),
            }
        )

    asking_why = any(
        phrase in user_question.lower()
        for phrase in ("why", "cause", "reason")
    )

    if asking_why and region_result is not None:
        top_region = max(
            region_result,
            key=lambda row: row["cancellation_rate_pct"],
        )
        return (
            f"{top_region['order_region'].strip()} had the highest observed "
            f"cancellation rate at {top_region['cancellation_rate_pct']}%. "
            "This regional breakdown does not show why orders were canceled. "
            "We would need more evidence, such as cancellation reasons or "
            "comparisons across periods, to investigate the cause."
        )

    if not tool_was_called:
        return response.output_text

    final_response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You are a supply chain analytics assistant. "
            "Explain the tool results using only the returned data. "
            "Distinguish cancellation rate from number of canceled orders. "
            "A breakdown by region describes where cancellations occurred; "
            "it does not establish why customers canceled. "
            "Do not claim a region caused or contributed disproportionately "
            "to a high monthly rate without a comparison or decomposition. "
            "When asked why, state what the data shows and what evidence "
            "would be needed to investigate the cause."
        ),
        input=input_messages,
    )

    return final_response.output_text


if __name__ == "__main__":
    print("Supply Chain AI Agent")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            print("Agent: Goodbye!")
            break

        if not question:
            continue

        answer = run_agent(question)

        print(f"\nAgent: {answer}\n")
