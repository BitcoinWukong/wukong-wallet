import asyncio
from datetime import datetime
from typing import Dict, List

from db.block_data import BlockData
from electrum_client import electrum_client
from kivy.logger import Logger


class BlockManager:
    def __init__(self) -> None:
        self.height_to_block: Dict[int, BlockData] = {}
        for block_data in BlockData.select():
            self.height_to_block[block_data.height] = block_data

    async def get_block(self, height: int) -> BlockData:
        if height <= 0:
            return None

        if height not in self.height_to_block:
            self.height_to_block[height] = BlockData.create(height=height)
            await self.update_block_header(height)
        return self.height_to_block[height]

    async def update_block_header(self, height: int):
        if height not in self.height_to_block:
            self.height_to_block[height] = BlockData.create(height=height)
        if self.height_to_block[height].header_hex is not None:
            return

        Logger.debug(f"Updating header for: {height}")
        header_hex = await electrum_client.rpc("blockchain.block.header", [str(height)])
        Logger.debug(f"Block header updated: {height}")

        blocktime = self.parse_blocktime(header_hex)
        self.height_to_block[height].header_hex = header_hex
        self.height_to_block[height].timestamp = blocktime
        self.height_to_block[height].save()

    def parse_blocktime(
        self,
        header_hex,
    ):
        return datetime.fromtimestamp(
            int.from_bytes(bytes.fromhex(header_hex)[68:72], "little")
        )

    def get_blocktime(self, height):
        if height in self.height_to_block:
            return self.height_to_block[height].timestamp
        else:
            return None

    async def update_block_headers(self, relevant_block_heights: List[int]):
        Logger.debug(f"Updating header for: {relevant_block_heights}")
        pending_tasks = []
        for height in relevant_block_heights:
            pending_tasks.append(asyncio.create_task(self.update_block_header(height)))
        await asyncio.gather(*pending_tasks)


_block_manager = None


def block_manager() -> BlockManager:
    global _block_manager
    if not _block_manager:
        _block_manager = BlockManager()
    return _block_manager
