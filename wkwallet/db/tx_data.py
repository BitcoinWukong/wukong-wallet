from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField
from pycoin.symbols.btc import network as BTC

from .base_model import BaseModel
from .wallet_data import WalletData


class TxData(BaseModel):
    wallet = ForeignKeyField(WalletData, backref="txs", on_delete="CASCADE")
    height = IntegerField(default=0)
    timestamp = DateTimeField(null=True)
    tx_id = CharField()

    hex = CharField(null=True)

    balance_change = IntegerField(default=0)
    is_processed = BooleanField(default=False)

    label = CharField(default="")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tx_object = None

    @property
    def tx_object(self):
        if self.hex is None:
            return None

        if self._tx_object is None:
            Tx = BTC.tx
            self._tx_object = Tx.from_hex(self.hex)
        return self._tx_object

    def __gt__(self, other):
        return self.timestamp is None or (
            other.timestamp is not None and self.timestamp > other.timestamp
        )
