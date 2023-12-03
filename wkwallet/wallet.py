import asyncio
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from db.account_data import AccountData
from db.address_data import AddressData
from db.tx_data import TxData
from db.utxo_data import UTXOData
from db.wallet_data import WalletData
from electrum_client import *
from kivy.logger import Logger
from model.block_manager import block_manager
from model.exchange_rate_manager import exchange_rate_manager
from model.fidelity_bond import lock_year_month_to_address_index
from model.script_type import ScriptType
from model.tx_manager import TxManager
from model.wallet_account import WalletAccount
from pycoin.coins.bitcoin.TxOut import TxOut as pycoin_tx_out
from pycoin.symbols.btc import network as BTC
from utils import bip_329_record, create_async_io_background_loop

MAX_TX_DETAILS_COUNT = 20
DEEP_REFRESH_GAP_LIMIT = 50
RECENT_ADDRESSES_TO_LOAD = 50


class Wallet:
    def __init__(self, wallet_data: WalletData):
        # Public properties
        self.data = wallet_data
        self._read_loop = create_async_io_background_loop()
        self._write_loop = create_async_io_background_loop()
        self._completed_loading = False

        # Basic info
        master_key = BTC.parse(self.data.accounts[0].xpub.strip())
        self._master_key = master_key
        self.xpub = self._master_key.as_text()

        # Accounts info
        self.accounts: Dict[int, WalletAccount] = {}
        acct_data: AccountData
        for acct_data in self.data.accounts:
            self.accounts[acct_data.account_index] = WalletAccount(acct_data)

        asyncio.run_coroutine_threadsafe(
            self.load_wallet_data(),
            self._read_loop,
        )

        self.addr_indexes_to_data = {}  # type: Dict[Tuple[int, int, int], AddressData]
        self._addr_str_to_data = {}  # type: Dict[str, AddressData]

        # Load active addresses and the most recent addresses
        Logger.info("Loading active addresses and most recent addresses ...")
        for acct_data in self.data.accounts:
            addr_data: AddressData

            # The address_data object in account.active_addresses and self.addr_indexes_to_data
            # must be the same one.
            for addr_data in acct_data.addresses.where(AddressData.is_active == True):
                self.accounts[acct_data.account_index].add_active_address(addr_data)
                self._addr_str_to_data[addr_data.address_str] = addr_data
                self.addr_indexes_to_data[addr_data.indexes_tuple()] = addr_data

            for chain_index in (0, 1):
                for addr_data in (
                    acct_data.addresses.where(
                        (AddressData.chain_index == chain_index)
                        & (AddressData.is_active == False)
                    )
                    .order_by(AddressData.address_index.desc())
                    .limit(RECENT_ADDRESSES_TO_LOAD)
                ):
                    self._addr_str_to_data[addr_data.address_str] = addr_data
                    self.addr_indexes_to_data[addr_data.indexes_tuple()] = addr_data

            self.accounts[acct_data.account_index].update_balance()
        self.total_balance = sum(account.balance for account in self.accounts.values())
        Logger.info("Loading active addresses and most recent addresses done")

        # Cache data for parsing transactions.
        self._address_to_tx_ids = {}  # type: Dict[AddressData, Set[str]]
        self._tx_id_to_balance_change = {}  # type: Dict[str, int]

        # Refresh tasks
        self._refresh_tasks: List[asyncio.Task] = []

    def save_data(self, data):
        async def save_data_async(data):
            data.save()

        asyncio.run_coroutine_threadsafe(save_data_async(data), self._write_loop)

    async def load_wallet_data(self) -> None:
        Logger.info(f"Initializing tx_manager...")
        self.tx_manager = TxManager(self.data)
        Logger.info(f"Initializing tx_manager done")
        self._completed_loading = True

    def set_wallet_name(self, name):
        self.data.name = name
        self.data.save()

    def is_hidden(self):
        return self.data.currency == "HIDDEN"

    def wallet_title(self):
        if self.data.name:
            return self.data.name
        else:
            return self.xpub[:10]

    def owns_address(self, address_str) -> bool:
        return self.get_address_data(address_str) is not None

    def get_address_data(self, address_str) -> Optional[AddressData]:
        if address_str not in self._addr_str_to_data:
            self._addr_str_to_data[address_str] = AddressData.get_or_none(
                AddressData.wallet == self.data,
                AddressData.address_str == address_str,
            )
        return self._addr_str_to_data[address_str]

    def new_internal_address_indexes(self):
        address_indexes = []

        for account_data in self.data.accounts:
            account_index = account_data.account_index
            account_address_indexes = [
                (account_index, 1, address_index)
                for address_index in range(
                    max(
                        0,
                        self.accounts[account_index].first_active_address_index(1) - 10,
                    ),
                    account_data.chains[1].first_unused_index + self.data.gap_limit,
                )
            ]
            Logger.info(
                f"[{self.wallet_title()}]: Refreshing "
                f"account {account_address_indexes[0][0]} "
                f"chain {account_address_indexes[0][1]} "
                f"from {account_address_indexes[0][2]} "
                f"to {account_address_indexes[-1][2]}"
            )
            address_indexes += account_address_indexes

        if self.data.has_fidelity_bonds:
            fidelity_bond_address_indexes = [
                (0, 2, address_index)
                for address_index in range(
                    lock_year_month_to_address_index(year=2030, month=12)
                )
            ]
            address_indexes += fidelity_bond_address_indexes
        return address_indexes

    def all_internal_address_indexes(self):
        address_indexes = []

        for account_data in self.data.accounts:
            account_index = account_data.account_index
            account_address_indexes = [
                (account_index, 1, address_index)
                for address_index in range(
                    0,
                    account_data.chains[1].first_unused_index + DEEP_REFRESH_GAP_LIMIT,
                )
            ]
            Logger.info(
                f"[{self.wallet_title()}]: Refreshing "
                f"account {account_index} chain 1 "
                f"from {account_address_indexes[0][2]} "
                f"to {account_address_indexes[-1][2]}"
            )
            address_indexes += account_address_indexes

        if self.data.has_fidelity_bonds:
            fidelity_bond_address_indexes = [
                (0, 2, address_index)
                for address_index in range(
                    lock_year_month_to_address_index(year=2030, month=12)
                )
            ]
            address_indexes += fidelity_bond_address_indexes
        return address_indexes

    def external_address_indexes(self):
        address_indexes = []

        for account_data in self.data.accounts:
            account_index = account_data.account_index
            account_address_indexes = [
                (account_index, 0, address_index)
                for address_index in range(
                    max(0, account_data.chains[0].first_unused_index - 20),
                    account_data.chains[0].first_unused_index + self.data.gap_limit,
                )
            ]
            Logger.info(
                f"[{self.wallet_title()}]: Refreshing "
                f"account {account_index} chain 0 "
                f"from {account_address_indexes[0][2]} "
                f"to {account_address_indexes[-1][2]}"
            )
            address_indexes += account_address_indexes
        return address_indexes

    def export_labels(self) -> List[str]:
        exported_labels = []

        # export wallle title as the label of account 0's xpub
        if self.data.name:
            exported_labels.append(
                bip_329_record(
                    type="xpub", ref=self.accounts[0].data.xpub, label=self.data.name
                )
            )

        # export all tx labels of this wallet
        tx_data: TxData
        for tx_data in self.data.txs.where(TxData.label != ""):
            exported_labels.append(
                bip_329_record(type="tx", ref=tx_data.tx_id, label=tx_data.label)
            )

        # export all address labels of this wallet
        addr_data: AddressData
        for addr_data in (
            AddressData.select()
            .join(AccountData)
            .where((AccountData.wallet == self.data) & (AddressData.label != ""))
        ):
            exported_labels.append(
                bip_329_record(
                    type="addr",
                    ref=addr_data.address_str,
                    label=addr_data.label,
                )
            )
        return exported_labels

    def refresh(self, refresh_callback=None):
        asyncio.run_coroutine_threadsafe(
            Wallet.refresh_async(self, refresh_callback),
            electrum_client.loop,
        )
        exchange_rate_manager.update_exchange_rate()

    @property
    def running_tasks_count(self):
        return len(self._refresh_tasks) - self._completed_refresh_tasks_count

    async def refresh_async(self, refresh_callback):
        # Sleep until the initial loading is completed
        while not self._completed_loading:
            await asyncio.sleep(1)

        Logger.info(f"[{self.wallet_title()}]: Refreshing wallet...")

        # Refresh tasks
        self._refresh_tasks = []
        self._pending_update_addr_index_tuples = []
        self._completed_refresh_tasks_count = 0

        # Reset balances
        self.processed_address_indexes = set()

        # Step 1: update the addresses info

        # Update all external addresses
        self.update_addresses_info(self.external_address_indexes())

        if self.data.completed_initial_sync:
            # Update only the active addresses and new addresses
            for account in self.accounts.values():
                address_index_tuples = [
                    address.indexes_tuple() for address in account.active_addresses
                ]
                self.update_addresses_info(address_index_tuples)
                Logger.info(
                    f"[{self.wallet_title()}]: Refreshing {address_index_tuples}"
                )

            self.update_addresses_info(self.new_internal_address_indexes())
        else:
            self.update_addresses_info(self.all_internal_address_indexes())

        finished_tasks_count = 0
        while finished_tasks_count < len(self._refresh_tasks):
            finished_tasks_count = len(self._refresh_tasks)
            await asyncio.gather(*self._refresh_tasks)

        Logger.info(f"[{self.wallet_title()}]: All address info updated.")
        self.save_account_data()

        # Step 2: update the block headers
        Logger.info(f"[{self.wallet_title()}]: Updating block headers...")
        await block_manager().update_block_headers(self.tx_manager.tx_heights())
        Logger.info(f"[{self.wallet_title()}]: All block headers updated.")

        # Step 3: fetch transaction details
        Logger.info(f"[{self.wallet_title()}]: Updating transactions details...")
        await self.fetch_transactions_details()
        Logger.info(f"[{self.wallet_title()}]: All transactions details updated.")

        self.finish_refresh()
        Logger.info(f"[{self.wallet_title()}]: Refresh completed.")

        if refresh_callback:
            refresh_callback(self)

    def update_pending_addresses(self):
        MAX_ADDRESSES_PER_REQUEST = 40
        MAX_CONCURRENT_REQUESTS_COUNT = 5

        while self.running_tasks_count < MAX_CONCURRENT_REQUESTS_COUNT:
            # No pending addreses to update
            if not self._pending_update_addr_index_tuples:
                break

            # Create refresh coroutines and append them to the pending list
            def task_completed(_):
                self._completed_refresh_tasks_count += 1
                Logger.debug(
                    f"[{self.wallet_title()}]: Pending update addresses: {len(self._pending_update_addr_index_tuples)}"
                )
                self.update_pending_addresses()

            task = asyncio.create_task(
                self.update_addresses_info_async(
                    self._pending_update_addr_index_tuples[:MAX_ADDRESSES_PER_REQUEST]
                )
            )
            self._pending_update_addr_index_tuples = (
                self._pending_update_addr_index_tuples[MAX_ADDRESSES_PER_REQUEST:]
            )
            self._refresh_tasks.append(task)
            Logger.debug(
                f"[{self.wallet_title()}]: Waiting for {self.running_tasks_count} tasks"
            )
            Logger.debug(
                f"[{self.wallet_title()}]: Pending update addresses: {len(self._pending_update_addr_index_tuples)}"
            )
            task.add_done_callback(task_completed)

    def update_addresses_info(self, address_index_tuples):
        self._pending_update_addr_index_tuples += reversed(address_index_tuples)
        self.update_pending_addresses()

    async def update_addresses_info_async(self, address_index_tuples):
        if not address_index_tuples:
            return

        requests = []
        callbacks = []
        for address_index_tuple in address_index_tuples:
            if address_index_tuple in self.processed_address_indexes:
                continue
            self.processed_address_indexes.add(address_index_tuple)

            # Get script_hash
            address_data = self.address_data_for_index_tuple(address_index_tuple)
            # During initial_sync, do not fetch address_data if it has already been
            # updated before and that it's not active at this moment.
            if (
                not self.data.completed_initial_sync
                and address_data.update_time is not None
                and not address_data.is_active
            ):
                Logger.debug(f"skip address {address_index_tuple}")
                continue
            else:
                Logger.debug(
                    f"{address_index_tuple}: address_data.update_time {address_data.update_time}"
                )
            script_hash = address_data.script_hash

            # Request for getting address balance
            requests.append((GET_BALANCE_RPC, script_hash))
            callbacks.append((self.update_address_balance, address_data, False))
            # Request for getting address history
            requests.append((GET_HISTORY_RPC, script_hash))
            callbacks.append((self.update_address_history, address_data, True))

        if not requests:
            return
        try:
            responses = await electrum_client.batch_rpc(requests)
        except Exception as e:
            raise e
        if len(responses) != len(callbacks):
            raise Exception("responses len doesn't match callbacks len")

        for i in range(len(responses)):
            (method, address_data, is_async) = callbacks[i]
            data = responses[i]
            if is_async:
                await method(address_data, data)
            else:
                method(address_data, data)

    def update_address_balance(self, address_data: AddressData, address_balance):
        account_index, chain_index = (
            address_data.account_index,
            address_data.chain_index,
        )

        confirmed_balance = address_balance["confirmed"]
        unconfirmed_balance = address_balance["unconfirmed"]
        latest_address_balance = confirmed_balance + unconfirmed_balance
        if latest_address_balance > 0:
            Logger.info(
                f"[{self.wallet_title()}]: balance @ {account_index}/{chain_index}/{address_data.address_index}: {latest_address_balance}"
            )

        if (
            confirmed_balance != address_data.confirmed_balance
            or unconfirmed_balance != address_data.pending_balance
        ):
            address_data.confirmed_balance = confirmed_balance
            address_data.pending_balance = unconfirmed_balance
            if confirmed_balance > 0 or unconfirmed_balance > 0:
                address_data.is_active = True
                self.accounts[account_index].add_active_address(address_data)
            else:
                address_data.is_active = False
                self.accounts[account_index].remove_active_address(address_data)
            self.save_data(address_data)

        # Special handling for fidelity bond active addresses
        if confirmed_balance > 0 and chain_index == 2:
            address_data.is_active = True
            self.save_data(address_data)
            self.accounts[account_index].add_active_address(address_data)

    # Process the tx history of an address.
    async def update_address_history(self, address_data: AddressData, address_history):
        account_index, chain_index, address_index = (
            address_data.account_index,
            address_data.chain_index,
            address_data.address_index,
        )

        # This address has tx history, update last_used_address_indexes and fetch info of more addresses.
        if chain_index in (0, 1) and len(address_history) > 0:
            account_data = self.data.accounts[account_index]
            chain_data = account_data.chains[chain_index]
            if not self.data.completed_initial_sync and chain_index != 0:
                gap_limit = DEEP_REFRESH_GAP_LIMIT
            else:
                gap_limit = (
                    self.data.gap_limit if chain_index == 0 else self.data.gap_limit
                )

            if address_index >= chain_data.first_unused_index:
                original_first_addr_index = chain_data.first_unused_index
                new_first_addr_index = address_index + 1
                chain_data.first_unused_index = new_first_addr_index
                chain_data.save()
                Logger.info(
                    (
                        f"[{self.wallet_title()}]: Refreshing "
                        f"account {account_index} "
                        f"chain {chain_index} "
                        f"from {original_first_addr_index + gap_limit} "
                        f"to {new_first_addr_index + gap_limit - 1}"
                    )
                )

                self.update_addresses_info(
                    [
                        (account_index, chain_index, address_index)
                        for address_index in range(
                            original_first_addr_index + gap_limit,
                            new_first_addr_index + gap_limit,
                        )
                    ]
                )

        # Update the update time of address_data
        address_data.update_time = datetime.now()
        self.save_data(address_data)

        # Store all txs to self.tx_manager and `address_to_tx_ids`
        self._address_to_tx_ids[address_data] = set()
        for history in address_history:
            height = history["height"]
            tx_id = history["tx_hash"]
            await self.tx_manager.add_tx_async(tx_id, height)
            self._address_to_tx_ids[address_data].add(tx_id)

    async def fetch_transactions_details(self) -> None:
        """
        Step 3: Fetch the tx details. We only fetch the most recent MAX_TX_DETAILS_COUNT
        txs to avoid long waiting on large wallets.
        """
        # TODO: allow continously fetching more and more tx histories.
        self.recent_tx_history: List[str] = []
        tx_to_process_ids = set()

        # Prepare `tx_to_process` and `recent_tx_history`
        for tx_id in self.tx_manager.pending_tx_ids:
            tx_to_process_ids.add(tx_id)
            self.recent_tx_history.append(tx_id)
            Logger.info(f"Unconfirmed Tx to process: {tx_id}")

        for height in reversed(sorted(self.tx_manager.tx_heights())):
            if len(self.recent_tx_history) >= MAX_TX_DETAILS_COUNT:
                break
            for tx_id in self.tx_manager.tx_ids_of_height(height):
                if len(self.recent_tx_history) >= MAX_TX_DETAILS_COUNT:
                    break
                if not self.tx_manager.has_parsed_tx(tx_id):
                    tx_to_process_ids.add(tx_id)
                    Logger.debug(f"tx_to_process: {tx_id}")
                else:
                    Logger.debug(f"tx already processed: {tx_id}")
                self.recent_tx_history.append(tx_id)

        # We should also parse all transactions related to the active paths
        additional_txs_to_process = []
        for account in self.accounts.values():
            for address in account.active_addresses:
                for tx_id in self._address_to_tx_ids[address]:
                    if tx_id not in tx_to_process_ids:
                        # if (
                        #     tx_id not in tx_to_process_ids
                        #     and not self.tx_manager.has_parsed_tx(tx_id)
                        # ):
                        tx_to_process_ids.add(tx_id)
                        additional_txs_to_process.append(tx_id)

        pending_tasks = []
        for tx_id in self.recent_tx_history:
            if self.tx_manager.tx_needs_parsing(tx_id):
                pending_tasks.append(asyncio.create_task(self.parse_transaction(tx_id)))
        for tx_id in additional_txs_to_process:
            if self.tx_manager.tx_needs_parsing(tx_id):
                pending_tasks.append(asyncio.create_task(self.parse_transaction(tx_id)))
        await asyncio.gather(*pending_tasks)

    async def parse_transaction(self, tx_id) -> None:
        tx_data: TxData = await self.tx_manager.get_tx_with_data(tx_id=tx_id)
        if tx_data is None:
            # This tx_id no longer exist in mempool, delete this tx completely from this
            # wallet
            self.tx_manager.remove_tx(tx_id)

            if tx_id in self.recent_tx_history:
                self.recent_tx_history.remove(tx_id)
            # TODO:Mark the address_data as inactive if needed.
            return

        address_for_script = BTC.address.for_script
        self._tx_id_to_balance_change[tx_id] = 0

        # If an output addresses belongs to the wallet, then the UTXO is received by us.
        tx_out: pycoin_tx_out
        for tx_index in range(len(tx_data.tx_object.txs_out)):
            tx_out = tx_data.tx_object.txs_out[tx_index]
            out_address = address_for_script(tx_out.puzzle_script())
            out_address_data = self.get_address_data(out_address)
            if out_address_data:
                Logger.debug(f"updating address status for {out_address}")
                # This UTXO is received by us.
                utxo_data = UTXOData.get_or_none(
                    UTXOData.tx == tx_data,
                    UTXOData.address == out_address_data,
                )
                if utxo_data is None:
                    utxo_data = UTXOData.create(
                        account=out_address_data.account,
                        address=out_address_data,
                        tx=tx_data,
                        tx_index=tx_index,
                        balance=tx_out.coin_value,
                    )
                self._tx_id_to_balance_change[tx_id] += tx_out.coin_value
                await self.update_utxo_address_status(
                    tx_data, utxo_data, out_address_data
                )

        # Chek all the tx inputs, and see if any of the input is involved in a tx that
        # this wallet has participated. If so, we should fetch that tx and see if the
        # spent input was a UTXO of this wallet.
        pre_tx_outs = []  # [ (tx_hash, tx_out_index) ]
        for tx_in in tx_data.tx_object.txs_in:
            pre_tx_id = str(tx_in.previous_hash)
            if self.tx_manager.contains_tx(tx_id=pre_tx_id):
                pre_index = tx_in.previous_index
                pre_tx_outs.append((pre_tx_id, pre_index))

        def deduct_tx_in_value(pre_tx_object, pre_index, cur_tx_id):
            # deduct the value if the output belongs to an address of this wallet
            pre_tx_out = pre_tx_object.txs_out[pre_index]
            pre_tx_out_address = address_for_script(pre_tx_out.puzzle_script())

            if self.owns_address(pre_tx_out_address):
                self._tx_id_to_balance_change[cur_tx_id] -= pre_tx_object.txs_out[
                    pre_index
                ].coin_value

        for pre_tx_id, pre_index in pre_tx_outs:
            pre_tx = await self.tx_manager.get_tx_with_data(tx_id=pre_tx_id)
            deduct_tx_in_value(
                pre_tx_object=pre_tx.tx_object,
                pre_index=pre_index,
                cur_tx_id=tx_id,
            )

    def get_txs(self, start_index=0, count=20) -> List[TxData]:
        end_index = start_index + count

        txs = []
        cur_index = 0

        # All pending transactions
        for tx_data in self.data.txs.where(TxData.height <= 0):
            Logger.debug(f"get_tx: {tx_data.tx_id}, UNCONFIRMED")

            if cur_index >= start_index:
                txs.append(tx_data)
            cur_index += 1
            if cur_index >= end_index:
                break

        # Other recent transactions
        for tx_data in self.data.txs.where(TxData.is_processed == True).order_by(
            TxData.height.desc()
        ):
            Logger.debug(f"get_tx: {tx_data.tx_id}, height: {tx_data.height}")

            if cur_index >= start_index:
                txs.append(tx_data)
            cur_index += 1
            if cur_index >= end_index:
                break
        return txs

    def finish_refresh(self):
        # Mark initial sync as completed
        self.data.completed_initial_sync = True
        self.data.save()

        # Update wallet balance

        for acct_data in self.data.accounts:
            self.accounts[acct_data.account_index].update_balance()
        self.total_balance = sum(account.balance for account in self.accounts.values())

        # Save the TxData
        for tx_id in self.recent_tx_history:
            if not self.tx_manager.has_parsed_tx(tx_id):
                self.tx_manager.mark_tx_as_parsed(
                    tx_id=tx_id, balance_change=self._tx_id_to_balance_change[tx_id]
                )

    def get_cj_value_and_count(self, tx_data: TxData):
        """
        Return (cj_value, cj_count) of raw_tx
        """
        cj_value, cj_count = None, 1
        for tx_out_i in tx_data.tx_object.txs_out:
            count = 0
            for tx_out_j in tx_data.tx_object.txs_out:
                if tx_out_j.coin_value == tx_out_i.coin_value:
                    count += 1
            if count > cj_count:
                cj_value, cj_count = tx_out_i.coin_value, count
        return cj_value, cj_count

    async def update_utxo_address_status(
        self,
        tx_data: TxData,
        utxo_data: UTXOData,
        address_data: AddressData,
    ):
        """
        Update the status of utxo_data and address_data for raw_tx
        """
        # If the tx_out is not a result of coin_join, we assume its anon_set_count is 1
        cj_value, cj_count = self.get_cj_value_and_count(tx_data)
        if utxo_data.balance != cj_value:
            utxo_data.anon_set_count = 1
        else:
            # For coin join output, we check its input to see if the input itself was also a coin join
            utxo_data.anon_set_count = cj_count
            await self.calc_pre_txs_anon_set_count(tx_data, utxo_data)
        utxo_data.save()

        # Update the status of address_data
        if address_data.chain_index == 2:
            address_data.status = "fidelity-bond"
        else:
            if len(address_data.utxos) > 1:
                address_data.status = "reused"
                Logger.debug(f"{address_data.address_str} reused")
            elif utxo_data.anon_set_count > 1:
                address_data.status = "coin-join"
                Logger.debug(f"{address_data.address_str} coin-join")
            elif cj_count > 1:
                # TODO: Make sure one of the tx_input belongs to this wallet
                address_data.status = "cj-change"
                Logger.debug(f"{address_data.address_str} cj-change")
            else:
                # TODO: Detect non-cj-change
                address_data.status = "deposit"
                Logger.debug(f"{address_data.address_str} deposit")
                await self.detect_deposit_or_change(address_data, tx_data)
        self.save_data(address_data)

    async def detect_deposit_or_change(
        self,
        address_data: AddressData,
        tx_data: TxData,
    ):
        # Save relevant input utxos to a list so that we can parse them later.
        input_utxos_to_parse = []  # [ (pre_tx_id, pre_tx_out_index) ]
        for tx_in in tx_data.tx_object.txs_in:
            pre_tx_id = str(tx_in.previous_hash)
            if self.tx_manager.contains_tx(tx_id=pre_tx_id):
                input_utxos_to_parse.append((pre_tx_id, tx_in.previous_index))

        async def parse_pre_tx_out(
            address_data: AddressData,
            pre_tx_data: TxData,
            pre_tx_out_index,
        ):
            pre_tx_out = pre_tx_data.tx_object.txs_out[pre_tx_out_index]

            # Only proceed when the previous tx_out belongs to us.
            pre_address = BTC.address.for_script(pre_tx_out.puzzle_script())
            if self.owns_address(pre_address):
                address_data.status = "non-cj-change"
                return

        # To parse the tx inputs, we need to fetch their own tx objects first.
        for pre_tx_id, pre_tx_out_index in input_utxos_to_parse:
            pre_tx_data = await self.tx_manager.get_tx_with_data(tx_id=pre_tx_id)
            await parse_pre_tx_out(
                address_data=address_data,
                pre_tx_data=pre_tx_data,
                pre_tx_out_index=pre_tx_out_index,
            )

    async def calc_pre_txs_anon_set_count(
        self,
        tx_data: TxData,
        dest_utxo_data: UTXOData,
    ):
        # Save relevant input utxos to a list so that we can parse them later.
        input_utxos_to_parse = []  # [ (pre_tx_id, pre_tx_out_index) ]
        for tx_in in tx_data.tx_object.txs_in:
            pre_tx_id = str(tx_in.previous_hash)
            if self.tx_manager.contains_tx(tx_id=pre_tx_id):
                input_utxos_to_parse.append((pre_tx_id, tx_in.previous_index))

        async def parse_pre_tx_out(
            pre_tx_data: TxData, pre_tx_out_index, dest_utxo_data: UTXOData
        ):
            # We only increase the anon_set_count if the input utxo is no less than the dest utxo.
            pre_tx_out = pre_tx_data.tx_object.txs_out[pre_tx_out_index]
            if pre_tx_out.coin_value < dest_utxo_data.balance:
                return

            # Only proceed when the previous tx_out belongs to us.
            pre_address = BTC.address.for_script(pre_tx_out.puzzle_script())
            if self.owns_address(pre_address):
                # If the inputs were the outputs of coin join themselves, we increase the
                # anon_set_count by the counter parties count of the previous coin join.
                cj_value, cj_count = self.get_cj_value_and_count(pre_tx_data)
                if pre_tx_out.coin_value == cj_value:
                    dest_utxo_data.anon_set_count += cj_count - 1
                    # This is a coin join, we recursively check its own input and see if they are coinjoin
                    # outputs as well.
                    await self.calc_pre_txs_anon_set_count(
                        pre_tx_data,
                        dest_utxo_data,
                    )

        # To parse the tx inputs, we need to fetch their own tx objects first.
        for pre_tx_id, pre_tx_out_index in input_utxos_to_parse:
            pre_tx_data = await self.tx_manager.get_tx_with_data(tx_id=pre_tx_id)
            await parse_pre_tx_out(
                pre_tx_data=pre_tx_data,
                pre_tx_out_index=pre_tx_out_index,
                dest_utxo_data=dest_utxo_data,
            )

    def get_deposit_address(self, delta=0) -> Tuple[str, str]:
        """
        Return: (addr_str, addr_path)
        """
        addr_index = self.data.accounts[0].chains[0].first_unused_index + delta
        addr_str = self.data.accounts[0].addr_str(chain_index=0, addr_index=addr_index)
        addr_path = f"0/{addr_index}"
        return (addr_str, addr_path)

    def save_account_data(self):
        with self.data._meta.database.atomic():
            self.data.save()
            for account_data in self.data.accounts:
                account_data.save()
                for chain_data in account_data.chains:
                    chain_data.save()

    def address_data_for_index_tuple(self, address_index_tuple) -> AddressData:
        if address_index_tuple in self.addr_indexes_to_data:
            return self.addr_indexes_to_data[address_index_tuple]

        account_index, chain_index, address_index = address_index_tuple

        address_data = AddressData.get_or_none(
            AddressData.wallet == self.data,
            AddressData.account_index == account_index,
            AddressData.chain_index == chain_index,
            AddressData.address_index == address_index,
        )
        if not address_data:
            Logger.debug(f"Creating address data for {address_index_tuple}")
            path = f"{chain_index}/{address_index}"
            address_str = self.data.accounts[account_index].addr_str(
                chain_index, address_index
            )

            address_data = AddressData(
                wallet=self.data,
                account=self.data.accounts[account_index],
                address_str=address_str,
                script_hash=self.accounts[account_index].ES_hash_for_path(path),
                account_index=account_index,
                chain_index=chain_index,
                address_index=address_index,
                path=path,
            )
        self.addr_indexes_to_data[address_index_tuple] = address_data
        self._addr_str_to_data[address_data.address_str] = address_data

        self.save_data(address_data)

        return self.addr_indexes_to_data[address_index_tuple]

    def enable_disable_fidelity_bonds(self, is_enabled):
        self.data.has_fidelity_bonds = is_enabled
        self.data.save()

        if not is_enabled:
            AddressData.delete().where(
                (AddressData.account == self.data.accounts[0])
                & (AddressData.chain_index == 2)
            ).execute()
            self.accounts[0].disable_fidelity_bonds()

        if is_enabled:
            self.accounts[0].chains[2] = ScriptType.WSH_FB
        elif 2 in self.accounts[0].chains:
            del self.accounts[0].chains[2]
