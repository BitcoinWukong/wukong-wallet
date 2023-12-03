#!/usr/bin/env python3

"""Electrum client library
"""
import asyncio
import logging
from time import sleep

from connectrum.client import StratumClient, ElectrumErrorResponse
from connectrum.svr_info import ServerInfo
from kivy.logger import Logger
from utils import create_async_io_background_loop

# logging.getLogger("connectrum").setLevel("INFO")
wklogger = logging.getLogger("wkwallet")


#########################################################################
# Electrum Server RPC APIs
#########################################################################
HEADER_SUBSCRIBE_RPC = "blockchain.headers.subscribe"

GET_BALANCE_RPC = "blockchain.scripthash.get_balance"
GET_HISTORY_RPC = "blockchain.scripthash.get_history"


#########################################################################
# ElectrumClient
#########################################################################
class ElectrumClient:
    """This class makes API calls to an Electrum server"""

    def __init__(self):
        self.server_info = None
        self.loop = create_async_io_background_loop()
        self.conn = StratumClient(loop=self.loop)

    def has_server_config(self):
        return self.server_info is not None

    def config_server(self, server_host_name):
        self.server_host_name = server_host_name
        # SSL
        # self.protocol = 's'
        # TCP
        self.protocol = "t"
        self.server_info = ServerInfo(
            server_host_name, server_host_name, ports=self.protocol
        )

    def conn_status(self):
        return f"{self.server_info}, {self.conn.server_version}, {self.conn.protocol_version}"

    def is_connected(self):
        return self.conn.protocol is not None

    async def connect_async(self):
        try:
            await self.conn.connect(
                self.server_info, self.protocol, disable_cert_verify=True
            )
        except Exception as e:
            Logger.warning("Unable to connect to server: %s" % e)
            return -1
        return 0

    # Electrum protocol methods:
    # https://electrumx-spesmilo.readthedocs.io/en/latest/protocol-methods.html
    async def rpc(self, method, args=[]):
        args = [(int(i) if i.isdigit() else i) for i in args]
        try:
            rpc_result = await self.conn.RPC(method, *args)
        except ElectrumErrorResponse as e:
            Logger.warning("RPC call failed: %s" % e)
            return None
        return rpc_result

    async def batch_rpc(self, requests):
        """
        Perform a batch of remote commands.
        Expects a list of ("method name", params...) tuples, where the method name should look
        like:
            blockchain.address.get_balance
        .. and sometimes take arguments, all of which are positional.
        Returns a list of results for each command from the server. Failures are returned as exceptions.
        """
        return await self.conn.batch_rpc(requests)

    async def get_script_hash_balance(self, script_hash):
        try:
            return await self.rpc("blockchain.scripthash.get_balance", [script_hash])
        except Exception as e:
            Logger.error(
                f"Unable to fetch script_hash balance {script_hash}, error: {e}"
            )
            raise e

    async def get_script_hash_history(self, script_hash):
        try:
            return await self.rpc("blockchain.scripthash.get_history", [script_hash])
        except Exception as e:
            Logger.error(
                f"Unable to fetch script_hash history {script_hash}, error: {e}"
            )
            raise e


#########################################################################
# ElectrumClient singleton
#########################################################################
electrum_client = ElectrumClient()


#########################################################################
# Main
#########################################################################
async def main():
    from model.crypt_utils import script_to_ES_hash
    from pycoin.symbols.btc import network as BTC

    server = "localhost"
    address_str = "bc1qc4sx0qywtft0vum8ep68ka6j6rfvhknltgvpvt"

    electrum_client.config_server(server)
    await electrum_client.connect_async()

    # Fetch the history of an arbitrary address
    key = BTC.parse.p2pkh_segwit(address_str)
    script = BTC.contract.for_p2pkh_wit(key.hash160())
    script_hash = script_to_ES_hash(script)

    address_history = await electrum_client.get_script_hash_history(script_hash)
    print(address_history)

    # subscribe_header_result = await electrum_client.rpc(HEADER_SUBSCRIBE_RPC)
    # print("subscribe_header_result:", subscribe_header_result)
    # relay_fee = await electrum_client.rpc("blockchain.relayfee")
    # print("relay_fee:", relay_fee)
    # balance = await electrum_client.get_balance(
    #     "8b01df4e368ea28f8dc0423bcf7a4923e3a12d307c875e47a0cfbf90b5c39161",
    # )
    # print("balance:", balance)


if __name__ == "__main__":
    asyncio.run_coroutine_threadsafe(main(), electrum_client.loop)

    while True:
        sleep(1)
