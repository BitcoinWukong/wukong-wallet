from datetime import datetime, timezone

from pycoin.symbols.btc import network as BTC


def lock_year_month_to_address_index(year, month):
    return (year - 2020) * 12 + month - 1


# 0: 2020/01/01
# 1: 2020/02/01
# 12: 2021/01/01
def address_index_to_locktime(address_index) -> datetime:
    year = 2020 + address_index // 12
    month = address_index % 12 + 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def time_lock_script(locktime: datetime, pubkey_hex):
    locktime_int = int(locktime.timestamp())
    return BTC.parse.script(
        f"{locktime_int} CHECKLOCKTIMEVERIFY DROP {pubkey_hex} CHECKSIG"
    ).script()
