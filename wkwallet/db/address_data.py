from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField

from .account_data import AccountData
from .base_model import BaseModel
from .wallet_data import WalletData


class AddressData(BaseModel):
    wallet = ForeignKeyField(WalletData, backref="addresses", on_delete="CASCADE")
    account = ForeignKeyField(AccountData, backref="addresses", on_delete="CASCADE")
    address_str = CharField()
    script_hash = CharField()

    account_index = IntegerField()
    chain_index = IntegerField()
    address_index = IntegerField()
    path = CharField()
    update_time = DateTimeField(null=True)

    label = CharField(default="")
    status = CharField(default="")

    is_active = BooleanField(default=False)

    confirmed_balance = IntegerField(default=0)
    pending_balance = IntegerField(default=0)

    def indexes_tuple(self):
        return (self.account_index, self.chain_index, self.address_index)

    @property
    def full_path(self) -> str:
        return str(self.account_index) + "/" + self.path

    @property
    def total_balance(self):
        return self.confirmed_balance + self.pending_balance

    @property
    def private_key(self):
        if self.account.wallet.seed_data is None:
            return None

        script_type = self.account.chain_script_type[self.chain_index]
        return self.account.wallet.seed_data.root_key.subkey_for_path(
            script_type.derivation_path()
        ).subkey_for_path(f"{self.account_index}p/{self.path}")
