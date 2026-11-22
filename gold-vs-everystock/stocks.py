"""Per-stock settings for the Gold vs Everystock videos.

Every event caption must be true in the data on the day it starts showing
(check with the numbers printed by fetch_data.py before adding one).
Caption windows must not overlap.
"""

START, END = "2016-11-21", "2026-11-19"

STOCKS = {
    "AAPL": dict(
        name="APPLE", label="Apple", color="#dfe4ee",
        events=[
            ("2019-01-03", "2019-04-20", "Late 2018: Apple drops 38%"),   # trough 2019-01-03
            ("2020-02-24", "2020-06-10", "2020: COVID crash"),
            ("2022-05-01", "2022-12-20", "2022: bear market"),
            ("2025-04-03", "2025-07-10", "April 2025: tariff selloff"),
            ("2026-01-29", "2026-04-30", "Jan 2026: gold hits record high"),  # GLD peak close
            ("2026-06-01", "2026-11-19", "Gold pulls back from its record"),
        ],
    ),
    "NKE": dict(
        name="NIKE", label="Nike", color="#4cc9f0",
        events=[
            ("2020-02-24", "2020-06-10", "2020: COVID crash"),
            ("2021-11-05", "2022-03-01", "Nov 2021: Nike hits all-time high"),  # peak $3,653
            ("2024-06-28", "2024-10-31", "Nike −20% in a day → gold takes lead"),
            ("2025-04-03", "2025-07-10", "April 2025: tariff selloff"),
            ("2026-01-29", "2026-03-25", "Jan 2026: gold hits record high"),
            ("2026-04-01", "2026-06-21", "Nike hovers around its $1,000 start"),  # crosses $1k 9x
            ("2026-06-22", "2026-09-30", "Nike sinks below its $1,000 start"),    # below from here on
            ("2026-10-02", "2026-11-19", "Nike is down over 75% from its peak"),  # −75%…−79% here
        ],
    ),
}
