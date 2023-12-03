from peewee import ForeignKeyField, IntegerField

from .account_data import AccountData
from .address_data import AddressData
from .base_model import BaseModel
from .tx_data import TxData


class UTXOData(BaseModel):
    account = ForeignKeyField(AccountData, backref="utxos")
    address = ForeignKeyField(AddressData, backref="utxos")
    tx = ForeignKeyField(TxData, backref="tx_outs", on_delete="CASCADE")
    tx_index = IntegerField()

    balance = IntegerField()
    anon_set_count = IntegerField(default=0)

    @property
    def tx_id(self) -> str:
        return self.tx.tx_id
