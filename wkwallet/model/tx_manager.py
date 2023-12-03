import asyncio
from typing import Dict, Iterator, Optional, Set

from db.tx_data import TxData
from db.wallet_data import WalletData
from electrum_client import electrum_client
from kivy.logger import Logger
from utils import create_async_io_background_loop

from .block_manager import block_manager


class TxManager:
    def __init__(self, wallet_data: WalletData) -> None:
        self._wallet_data = wallet_data
        self._loop = create_async_io_background_loop()

        self._tx_id_set: Set[str] = set()
        self._parsed_tx_ids: Set[str] = set()
        self._pending_tx_ids: Set[str] = set()
        self._height_to_tx_ids: Dict[int, Set[str]] = {}

        self._tx_id_to_data: Dict[str, TxData] = {}
        self._tx_id_to_event: Dict[str, asyncio.Event] = {}

        for tx_data in wallet_data.txs:
            tx_id = tx_data.tx_id
            self._tx_id_set.add(tx_id)
            self._tx_id_to_data[tx_id] = tx_data
            if tx_data.is_processed:
                self._parsed_tx_ids.add(tx_id)
            if tx_data.height <= 0:
                self._pending_tx_ids.add(tx_id)
            else:
                if self._height_to_tx_ids.get(tx_data.height) is None:
                    self._height_to_tx_ids[tx_data.height] = set()
                self._height_to_tx_ids[tx_data.height].add(tx_id)

    def save_data(self, data):
        async def save_data_async(data):
            data.save()

        asyncio.run_coroutine_threadsafe(save_data_async(data), self._loop)

    def tx_heights(self):
        return self._height_to_tx_ids.keys()

    def tx_ids_of_height(self, height: int):
        return self._height_to_tx_ids[height]

    def remove_tx(self, tx_id: str) -> None:
        if tx_id in self._pending_tx_ids:
            self._pending_tx_ids.remove(tx_id)

        if tx_id in self._tx_id_to_data:
            self._tx_id_to_data[tx_id].delete_instance(recursive=True)
            del self._tx_id_to_data[tx_id]

    def get_tx(self, tx_id: str) -> Optional[TxData]:
        return self._tx_id_to_data.get(tx_id)

    @property
    def pending_tx_ids(self) -> Iterator[str]:
        return (tx_id for tx_id in self._pending_tx_ids)

    def tx_needs_parsing(self, tx_id: str) -> bool:
        return (tx_id not in self._parsed_tx_ids) or (tx_id in self._pending_tx_ids)

    async def add_tx_async(self, tx_id: str, height: int) -> None:
        block = await block_manager().get_block(height)

        if tx_id not in self._tx_id_to_data:
            self._tx_id_to_data[tx_id] = TxData(
                wallet=self._wallet_data,
                height=height,
                tx_id=tx_id,
            )
            self.save_data(self._tx_id_to_data[tx_id])

        if tx_id not in self._tx_id_set:
            self._tx_id_set.add(tx_id)
        if height <= 0:
            # Unconfirmed Tx
            self._pending_tx_ids.add(tx_id)
        else:
            # Confirmed Tx
            if self._height_to_tx_ids.get(height) is None:
                self._height_to_tx_ids[height] = set()
            self._height_to_tx_ids[height].add(tx_id)

            if tx_id in self._pending_tx_ids:
                self._pending_tx_ids.remove(tx_id)

        if block is not None and (self._tx_id_to_data[tx_id].timestamp is None):
            # Update the height and timestamp of the tx_data
            self._tx_id_to_data[tx_id].height = height
            self._tx_id_to_data[tx_id].timestamp = block.timestamp
            self.save_data(self._tx_id_to_data[tx_id])
            Logger.debug(
                f"Saved block for raw_tx: {tx_id}, block: {block}, height: {height}"
            )

    async def get_tx_with_data(self, tx_id) -> Optional[TxData]:
        if tx_id not in self._tx_id_to_data:
            self._tx_id_to_data[tx_id] = TxData(
                wallet=self._wallet_data,
                tx_id=tx_id,
            )
            self.save_data(self._tx_id_to_data[tx_id])
        # Return the tx_object directly if it is a confirmed tx
        if (
            self._tx_id_to_data[tx_id].tx_object is not None
            and self._tx_id_to_data[tx_id].height > 0
        ):
            return self._tx_id_to_data[tx_id]

        tx_data = self._tx_id_to_data[tx_id]

        if tx_id not in self._tx_id_to_event:
            event = asyncio.Event()
            self._tx_id_to_event[tx_id] = event
            try:
                tx_data.hex = await electrum_client.rpc(
                    "blockchain.transaction.get", [tx_id]
                )
                if tx_data.hex is None:
                    return None
                tx_data.save()
            except Exception as e:
                Logger.error(f"Unable to fetch tx {tx_id}, error: {e}")

                tx_data.delete_instance(recursive=True)
                del self._tx_id_to_data[tx_id]
                tx_data = None
            event.set()
        else:
            await self._tx_id_to_event[tx_id].wait()
            tx_data = self._tx_id_to_data.get(tx_id)
        return tx_data

    def contains_tx(self, tx_id: str) -> bool:
        return tx_id in self._tx_id_set

    def has_parsed_tx(self, tx_id: str) -> bool:
        return tx_id in self._parsed_tx_ids

    def mark_tx_as_parsed(self, tx_id: str, balance_change: int) -> None:
        tx_data = self._tx_id_to_data.get(tx_id)
        if not tx_data:
            return

        if tx_id not in self._parsed_tx_ids:
            tx_data.balance_change = balance_change
            tx_data.is_processed = True
            tx_data.save()

            self._parsed_tx_ids.add(tx_id)
