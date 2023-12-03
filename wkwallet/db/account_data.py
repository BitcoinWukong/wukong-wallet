from typing import Dict

from kivy.logger import Logger
from model.script_type import ScriptType, script_types
from peewee import BlobField, CharField, ForeignKeyField, IntegerField
from pycoin.symbols.btc import network as BTC

from .base_model import BaseModel
from .wallet_data import WalletData


class AccountData(BaseModel):
    wallet = ForeignKeyField(WalletData, backref="accounts")

    account_index = IntegerField()
    xpub = CharField()
    master_fingerprint = BlobField(default=b"\x00\x00\x00\x00")
    origin_path = CharField(default="84p/0p/0p")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.master_pub_key = BTC.parse(self.xpub)
        self.chain_script_type: Dict[int, ScriptType] = {}
        for chain_data in self.chains:
            self.chain_script_type[chain_data.chain_index] = script_types[
                chain_data.script_type_name
            ]
            if self.wallet.has_fidelity_bonds:
                self.chain_script_type[2] = ScriptType.WSH_FB

    def script_object(
        self,
        chain_index: int,
        addr_index: int,
    ) -> ScriptType.BaseScriptType:
        if not chain_index in self.chain_script_type:
            return None

        script_type = self.chain_script_type[chain_index]
        key = self.master_pub_key.subkey_for_path(f"{chain_index}/{addr_index}")
        return script_type(key, addr_index)

    def addr_str(self, chain_index: int, addr_index: int) -> str:
        script_object = self.script_object(chain_index, addr_index)
        if not script_object:
            Logger.error(
                f"Invalid chain_index {chain_index} or addr_index {addr_index}"
            )
            raise ValueError(
                f"Invalid chain_index {chain_index} or addr_index {addr_index}"
            )
        return script_object.address()

    def get_unused_change_address(self) -> str:
        addr_index = self.chains[1].first_unused_index
        return self.addr_str(chain_index=1, addr_index=addr_index)
