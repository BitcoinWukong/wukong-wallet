from collections import namedtuple

TxSummaryRow = namedtuple(
    "TxSummaryRow",
    [
        "tx_data",
        "tx_icon",
        "tx_color",
        "tx_time",
        "balance_change",
    ],
)
