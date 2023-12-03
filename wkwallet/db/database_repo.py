from typing import List, Set

from peewee import Model, SqliteDatabase
from playhouse.sqliteq import SqliteQueueDatabase


from .account_data import AccountData
from .address_data import AddressData
from .base_model import setup_database_proxy
from .block_data import BlockData
from .chain_data import ChainData
from .seed_data import SeedData
from .tx_data import TxData
from .utxo_data import UTXOData
from .wallet_data import WalletData

DB_LOCATION_MEMORY = ":memory:"


class DatabaseRepo:
    def __init__(self, path_to_db, use_queued_db=False) -> None:
        if use_queued_db:
            self.db = SqliteQueueDatabase(path_to_db)
        else:
            self.db = SqliteDatabase(path_to_db)
        setup_database_proxy(self.db)

        self.db.create_tables(
            [
                BlockData,
                UTXOData,
                SeedData,
                WalletData,
                AccountData,
                ChainData,
                AddressData,
                TxData,
            ]
        )
        self.pending_objects_to_save: Set[Model] = set()
        self.pending_objects_to_delete: Set[Model] = set()

    def is_connected(self) -> bool:
        return self.db.is_connection_usable()

    def get_wallets(self) -> List[WalletData]:
        return WalletData.select()

    def get_accounts(self) -> List[AccountData]:
        return AccountData.select()

    def add_wallet(self) -> WalletData:
        wallet_data = WalletData()
        self.pending_objects_to_save.add(wallet_data)
        return wallet_data

    def add_account(self, wallet_data, account_index, xpub) -> AccountData:
        if wallet_data.id is None:
            raise ValueError("wallet_data must have a valid id")

        account_data = AccountData(
            wallet=wallet_data, account_index=account_index, xpub=xpub
        )
        self.pending_objects_to_save.add(account_data)
        return account_data

    def update(self, data_to_update: Model):
        self.pending_objects_to_save.add(data_to_update)

    def delete(self, data_to_delete: Model):
        self.pending_objects_to_delete.add(data_to_delete)

    def commit(self):
        with self.db.atomic():
            for pending_object in self.pending_objects_to_save:
                pending_object.save()
            self.pending_objects_to_save.clear()

            for pending_object in self.pending_objects_to_delete:
                pending_object.delete_instance(recursive=True, delete_nullable=True)
            self.pending_objects_to_delete.clear()
