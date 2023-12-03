import asyncio

from bitcoin.core import CMutableTransaction
from electrum_client import electrum_client
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from model.crypt_utils import bytes_to_hex

Builder.load_file("view/create_tx_view.kv")


class CreateTxView(Screen):
    tx_object: CMutableTransaction = ObjectProperty()
    tx_hex_label = ObjectProperty()

    def __init__(self, **kw):
        self.allowed_balance = 0
        self.back_view_name = "send_bitcoin_view"
        super().__init__(**kw)

    def on_pre_enter(self, *args):
        self.tx_hex_label.text = bytes_to_hex(self.tx_object.serialize())
        return super().on_pre_enter(*args)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = self.back_view_name

    def press_broadcast(self) -> None:
        async def broadcast_tx(raw_tx_hex):
            result = await electrum_client.rpc(
                "blockchain.transaction.broadcast", [raw_tx_hex]
            )
            Logger.info(f"Broadcasting Tx: {result}")
            self.back_view_name = "wallet_view"
            Clock.schedule_once(lambda dt: self.back())

        asyncio.run_coroutine_threadsafe(
            broadcast_tx(self.tx_hex_label.text),
            electrum_client.loop,
        )
