from abc import abstractmethod
from typing import List, Set

from db.account_data import AccountData
from db.address_data import AddressData
from db.chain_data import ChainData
from db.seed_data import SeedData
from db.tx_data import TxData
from db.wallet_data import WalletData
from kivy.logger import Logger
from model.crypt_utils import mnemonic_to_seed
from model.script_type import ScriptType
from pycoin.symbols.btc import network as BTC
from utils import bip_329_record
from wallet import Wallet


def verify_xpub(xpub: str) -> bool:
    if not xpub:
        return False
    master_key = BTC.parse(xpub.strip())
    if not master_key:
        return False
    return True


class WalletsObserver:
    @abstractmethod
    def on_balance_updated(self):
        pass

    @abstractmethod
    def on_tx_summaries_updated(self, refreshing_wallets):
        pass


class WalletManager:
    def __init__(self) -> None:
        self.wallets = []  # type: List[Wallet]
        for wallet_data in WalletData.select():
            self.open_wallet(wallet_data)

        self.is_refreshing = False
        self.refreshing_wallets: List[Wallet] = []
        self.observers = set()  # type: Set[WalletsObserver]

    def create_wallet_from_mnemonic(
        self,
        mnemonic: str,
        script_type: ScriptType.BaseScriptType = ScriptType.WPKH,
        n_accounts=1,
    ) -> Wallet:
        if not mnemonic_to_seed(mnemonic):
            return None

        # Create WalletData object
        seed_data = SeedData.create(mnemonic=mnemonic)
        wallet_data = WalletData.create(seed_data=seed_data)

        # Create AccountData objects
        accounts_root_key = seed_data.root_key.subkey_for_path(
            script_type.derivation_path()
        )
        for account_index in range(n_accounts):
            account_key = accounts_root_key.subkey_for_path(f"{account_index}p")
            xpub = account_key.as_text()
            account_info = AccountData.create(
                wallet=wallet_data,
                account_index=account_index,
                xpub=xpub,
            )
            for i in (0, 1):
                ChainData.create(
                    account=account_info,
                    chain_index=i,
                    script_type_name=script_type.script_type_name(),
                )
            account_index += 1

        new_wallet = Wallet(wallet_data)
        self.wallets.append(new_wallet)
        return new_wallet

    def create_watch_only_wallet(
        self,
        xpubs: List[str],
        script_type: ScriptType.BaseScriptType = ScriptType.WPKH,
    ) -> Wallet:
        for xpub in xpubs:
            if not verify_xpub(xpub):
                return None

        wallet_data = WalletData.create()

        # Create accounts from xpubs
        account_index = 0
        for xpub in xpubs:
            account_data = AccountData.create(
                wallet=wallet_data,
                account_index=account_index,
                xpub=xpub,
            )
            for i in (0, 1):
                ChainData.create(
                    account=account_data,
                    chain_index=i,
                    script_type_name=script_type.script_type_name(),
                )
            account_index += 1

        new_wallet = Wallet(wallet_data)
        self.wallets.append(new_wallet)
        return new_wallet

    def open_wallet(self, wallet_data: WalletData):
        Logger.info(f"Opening wallet {wallet_data.name}...")
        self.wallets.append(Wallet(wallet_data))
        Logger.info(f"Opening wallet {wallet_data.name} Done")

    def remove_wallet(self, wallet_info: WalletData):
        for wallet in self.wallets:
            if wallet.data == wallet_info:
                wallet.data.delete_instance(recursive=True)
                self.wallets.remove(wallet)

    def register_observer(self, wallets_observer: WalletsObserver):
        self.observers.add(wallets_observer)

    def deregister_observer(self, wallets_observer: WalletsObserver):
        if wallets_observer in self.observers:
            self.observers.remove(wallets_observer)

    def export_labels(self) -> List[str]:
        exported_labels = []
        # export all tx labels
        tx_data: TxData
        for tx_data in TxData.select().where(TxData.label != ""):
            exported_labels.append(
                bip_329_record(type="tx", ref=tx_data.tx_id, label=tx_data.label)
            )

        # export all address labels
        addr_data: AddressData
        for addr_data in AddressData.select().where(AddressData.label != ""):
            exported_labels.append(
                bip_329_record(
                    type="addr",
                    ref=addr_data.address_str,
                    label=addr_data.label,
                )
            )
        return exported_labels

    def refresh(self, target_wallets=[]) -> None:
        Logger.info("WKWallet: Refresh started.")
        self.is_refreshing = True
        self.pending_wallets = set()
        if not target_wallets:
            target_wallets = self.wallets
        self.refreshing_wallets = target_wallets

        for wallet in target_wallets:
            Logger.info(f"WKWallet: Refreshing wallet: {wallet.wallet_title()}")
            wallet.refresh(
                self.on_wallet_refresh_completed,
            )
            self.pending_wallets.add(wallet)

    def on_wallet_refresh_completed(self, wallet):
        # TODO: differntiate the initial UI update and the actual refresh completion.
        if wallet in self.pending_wallets:
            self.pending_wallets.remove(wallet)
        if not self.pending_wallets:
            Logger.info("WKWallet: All wallets have completed refreshing.")
            self.is_refreshing = False
            for wallets_observer in self.observers:
                wallets_observer.on_tx_summaries_updated(self.refreshing_wallets)
            self.refreshing_wallets = []
        else:
            for wallet in self.pending_wallets:
                Logger.info(f"WKWallet: Pending wallet:{wallet.wallet_title()}")

    def update_tx_summaries(self, target_wallets: List[Wallet] = []):
        if not target_wallets:
            target_wallets = self.wallets

        for wallets_observer in self.observers:
            wallets_observer.on_tx_summaries_updated(target_wallets)


_wallet_manager = None


def wallet_manager() -> WalletManager:
    global _wallet_manager
    if not _wallet_manager:
        _wallet_manager = WalletManager()
    return _wallet_manager
