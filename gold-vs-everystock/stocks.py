"""Per-stock settings for the Gold vs Everystock videos.

Every event caption must be true in the data on the day it starts showing
(check with the numbers printed by fetch_data.py before adding one).
Caption windows must not overlap.

Optional keys: "note" replaces the footer's "<label> incl. reinvested dividends"
line (e.g. for assets without dividends); "slug" names the output file.
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
    "BTC-USD": dict(
        name="BITCOIN", label="Bitcoin", color="#a98bff", slug="btc",
        # purple, not Bitcoin orange: orange is too close to the gold line
        note="Bitcoin = BTC-USD close",
        events=[
            ("2017-12-18", "2018-03-15", "Dec 2017: Bitcoin bubble peaks"),
            ("2018-12-14", "2019-03-31", "2018: Bitcoin crashes 83%"),          # 2017 peak -> trough
            ("2020-03-12", "2020-05-31", "Mar 2020: Bitcoin −37% in one day"),
            ("2021-11-08", "2022-02-28", "Nov 2021: new all-time high"),
            ("2022-11-21", "2023-02-28", "2022: crypto winter, −77%"),          # trough 2022-11-21
            ("2024-01-11", "2024-03-31", "Jan 2024: Bitcoin ETFs launch"),
            ("2025-10-06", "2026-01-15", "Oct 2025: Bitcoin record high"),
            ("2026-01-29", "2026-03-25", "Jan 2026: gold hits record high"),
            ("2026-06-30", "2026-09-15", "June 2026: Bitcoin −53% from record"),  # trough 2026-06-30
        ],
    ),
    "KO": dict(
        name="COCA-COLA", label="Coca-Cola", color="#ff5a5f",
        events=[
            ("2020-03-23", "2020-06-10", "2020: COVID crash, Coke −37%"),
            ("2020-12-08", "2021-03-02", "Late 2020: gold pulls ahead"),
            ("2022-08-19", "2022-11-30", "Aug 2022: Coke leads by $490"),
            ("2024-10-21", "2025-01-31", "Oct 2024: gold retakes the lead"),
            ("2026-01-28", "2026-04-30", "Jan 2026: gold leads by $1,916"),
            ("2026-10-30", "2026-11-19", "Oct 2026: the Coca-Cola comeback!"),
        ],
    ),
    "NVDA": dict(
        name="NVIDIA", label="NVIDIA", color="#8be04e",
        events=[
            ("2018-12-24", "2019-03-31", "Late 2018: NVIDIA −56%"),             # 2018-10-01 -> 12-24
            ("2020-03-16", "2020-06-10", "2020: COVID crash"),
            ("2021-10-25", "2021-12-31", "Oct 2021: NVIDIA passes $10,000"),
            ("2022-10-14", "2023-01-31", "2022: NVIDIA −66%"),                  # 2021-11-29 -> 2022-10-14
            ("2023-05-25", "2023-09-30", "May 2023: AI boom, +24% in a day"),
            ("2024-05-29", "2024-09-30", "May 2024: NVIDIA passes $50,000"),
            ("2025-01-27", "2025-03-31", "Jan 2025: DeepSeek shock, −17% in a day"),
            ("2025-04-04", "2025-07-10", "April 2025: tariff selloff"),
            ("2026-05-14", "2026-08-31", "May 2026: NVIDIA passes $100,000"),
            ("2026-10-06", "2026-11-19", "Oct 2026: NVIDIA's all-time high"),
        ],
    ),
    "DIS": dict(
        name="DISNEY", label="Disney", color="#4f8cff",
        events=[
            ("2020-03-23", "2020-06-10", "2020: COVID crash, Disney −42%"),
            ("2021-03-08", "2021-06-30", "Mar 2021: Disney's all-time high"),
            ("2022-03-04", "2022-07-31", "Mar 2022: gold takes the lead for good"),
            ("2022-11-09", "2023-01-31", "Nov 2022: Disney −13% in a day"),
            ("2023-10-04", "2024-01-31", "Oct 2023: Disney −61% from its peak"),
            ("2026-01-29", "2026-03-25", "Jan 2026: gold hits record high"),
        ],
    ),
}
