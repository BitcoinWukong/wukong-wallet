from typing import Any, Dict, Optional, Set, Type

from db.account_data import AccountData
from db.address_data import AddressData
from db.chain_data import ChainData
from pycoin.symbols.btc import network as BTC

from .script_type import ScriptType, script_types


class WalletAccount:
    @classmethod
    def create_account(
        cls,
        xpub: str,
        chains: Dict[int, Type[ScriptType.BaseScriptType]],
        master_fingerprint=b"\x00\x00\x00\x00",
        origin_path="84p/0p/0p",
    ):
        account_info = AccountData.create(
            account_index=0,
            xpub=xpub,
            master_fingerprint=master_fingerprint,
            origin_path=origin_path,
        )
        for chain_index in chains:
            ChainData.create(
                account=account_info,
                chain_index=chain_index,
                script_type_name=chains[chain_index].script_type_name(),
            )
        return WalletAccount(account_info)

    def __init__(
        self,
        account_data: AccountData,
    ) -> None:
        self.data = account_data

        self.xpub = account_data.xpub
        self.master_key = BTC.parse(self.xpub)
        self.chains = {}  # type: Dict[int, Any]
        for chain_data in account_data.chains:
            self.chains[chain_data.chain_index] = script_types[
                chain_data.script_type_name
            ]
        self.active_addresses: Set[AddressData] = set()
        self.balance = 0

        # Special handling of fidelity bonds for account 0
        if self.data.account_index == 0:
            if self.data.wallet and self.data.wallet.has_fidelity_bonds:
                self.chains[2] = ScriptType.WSH_FB
            else:
                self.disable_fidelity_bonds()

    def update_balance(self):
        self.balance = sum(
            addr_data.total_balance for addr_data in self.active_addresses
        )

    def first_active_address_index(self, chain_index: int):
        first_index = None
        for address_data in self.active_addresses:
            if address_data.chain_index == chain_index and (
                first_index is None or address_data.address_index < first_index
            ):
                first_index = address_data.address_index
        if first_index is None:
            first_index = 0
        return first_index

    def add_active_address(self, address_data: AddressData):
        self.active_addresses.add(address_data)

    def remove_active_address(self, address_data: AddressData):
        if address_data in self.active_addresses:
            self.active_addresses.remove(address_data)

    def disable_fidelity_bonds(self):
        self.active_addresses = set(
            filter(
                lambda address_info: address_info.chain_index != 2,
                self.active_addresses,
            )
        )

    def delete_instance(self):
        self.data.delete_instance(recursive=True)

    def script_object_for_path(self, path: str) -> ScriptType.BaseScriptType:
        chain_index, address_index = path.split("/")
        chain_index, address_index = int(chain_index), int(address_index)

        if not chain_index in self.chains:
            return None

        script_type = self.chains[chain_index]
        key = self.master_key.subkey_for_path(path)
        return script_type(key, address_index)

    def address_for_path(self, path: str) -> Optional[str]:
        script_object = self.script_object_for_path(path)
        if script_object:
            return script_object.address()
        else:
            return None

    def ES_hash_for_path(self, path: str):
        script_object = self.script_object_for_path(path)
        if script_object:
            return script_object.ES_hash()
