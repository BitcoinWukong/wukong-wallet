import asyncio

import requests
from electrum_client import electrum_client
from kivy.logger import Logger

SATS_PER_COIN = 100000000


def toggle_currency(currency, allow_hidden=True):
    if currency == "sat":
        return "BTC"
    elif currency == "BTC":
        return "USD"
    elif currency == "USD":
        if allow_hidden:
            return "HIDDEN"
        else:
            return "sat"
    else:
        return "sat"


class ExchangeRateManager:
    def __init__(self) -> None:
        self.__usd_rate = None
        self.update_exchange_rate()

    def update_exchange_rate(self):
        asyncio.run_coroutine_threadsafe(
            self.update_exchange_rate_async(),
            electrum_client.loop,
        )

    async def update_exchange_rate_async(self):
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, requests.get, "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
        )
        self.__usd_rate = response.json()["bpi"]["USD"]["rate_float"]
        Logger.info(f"WKWallet: USD exchange rate updated: {self.__usd_rate}")

    @property
    def usd_rate(self):
        return self.__usd_rate

    def format_balance(self, balance_in_sats: int, currency: str, allow_fiat=True):
        if not allow_fiat:
            if currency == "USD":
                currency = "sat"

        if currency == "USD":
            if self.usd_rate is None:
                return "$ -"
            else:
                usd_balance = (
                    balance_in_sats / SATS_PER_COIN * exchange_rate_manager.usd_rate
                )
                return f'${"{:,.2f}".format(usd_balance)}'
        elif currency == "BTC":
            return f'{"{:,.8f}".format(balance_in_sats/100000000)} BTC'
        elif currency == "HIDDEN":
            return "hidden sats"
        else:
            return f'{"{:,}".format(balance_in_sats)} sats'


exchange_rate_manager = ExchangeRateManager()
