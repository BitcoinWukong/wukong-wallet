import hashlib
import math
from typing import List, Tuple

from bitcoin.core import (
    CMutableOutPoint,
    CMutableTransaction,
    CMutableTxIn,
    CMutableTxOut,
)
from bitcoin.wallet import CBitcoinAddress
from mnemonic import Mnemonic
from pycoin.symbols.btc import network as BTC
from enum import Enum, auto

BIP32_PRV_PREFIX_HEX = b"\x04\x88\xAD\xE4"
BIP32_PUB_PREFIX_HEX = b"\x04\x88\xB2\x1E"
BIP49_PRV_PREFIX_HEX = b"\x04\x9D\x78\x78"
BIP49_PUB_PREFIX_HEX = b"\x04\x9D\x7C\xB2"
BIP84_PRV_PREFIX_HEX = b"\x04\xB2\x43\x0C"
BIP84_PUB_PREFIX_HEX = b"\x04\xB2\x47\x46"


class AddressType(Enum):
    PKH = auto()
    SH = auto()
    WPKH = auto()
    WSH = auto()


def bytes_to_hex(bytes):
    return "".join(format(x, "02x") for x in bytes)


def hex_to_bytes(hex_string):
    return bytearray.fromhex(hex_string)


def get_address_type(addr_str: str) -> AddressType:
    pycoin_object = BTC.parse(addr_str.strip())
    if pycoin_object:
        pycoin_addr_type = pycoin_object.info()["type"]
        if pycoin_addr_type == "p2pkh_wit":
            return AddressType.WPKH
        elif pycoin_addr_type == "p2sh_wit":
            return AddressType.WSH
        elif pycoin_addr_type == "p2sh":
            return AddressType.SH
    raise ValueError(f"Invalid address string: {addr_str}")


# Convert a Bitcoin Script to the Electrum Server protocol script hash.
def script_to_ES_hash(script: str):
    script_hash = bytearray(hashlib.sha256(script).digest())
    script_hash.reverse()  # Electrum Server protocol hash is little endian
    return bytes_to_hex(script_hash)


def mnemonic_to_seed(mnemonic):
    m = Mnemonic("english")
    return m.to_seed(mnemonic)


def mnemonic_to_root_key(mnemonic):
    seed = mnemonic_to_seed(mnemonic)
    seed_hex = bytes_to_hex(seed)
    return BTC.parse.bip32_seed("H:" + seed_hex)


def xpub_to_zpub(xpub):
    import base58

    return base58.b58encode_check(
        BIP84_PUB_PREFIX_HEX + base58.b58decode_check(xpub)[4:]
    ).decode("ascii")


def create_transaction(input_list, tx_outs_list) -> CMutableTransaction:
    version = 1
    locktime = 0
    vin = []
    vout = []

    sequence = 0xFFFFFFFD
    for utxo_data, _ in input_list:
        outpoint = CMutableOutPoint(
            # The tx_hash bytes needs to be converted to little endian
            hex_to_bytes(utxo_data.tx.tx_id)[::-1],
            utxo_data.tx_index,
        )
        tx_in = CMutableTxIn(prevout=outpoint, nSequence=sequence)
        vin.append(tx_in)
    for value, target_address in tx_outs_list:
        try:
            script_pubkey = CBitcoinAddress(target_address).to_scriptPubKey()
        except:
            return None
        tx_out = CMutableTxOut(value, script_pubkey)
        vout.append(tx_out)

    return CMutableTransaction(vin, vout, nLockTime=locktime, nVersion=version)


def sign_transaction(tx: CMutableTransaction, priv_key):
    pass


def estimate_tx_fee(
    tx_inputs_count: int,
    tx_output_addr_strs: List[str],
    sats_per_vbyte: int,
) -> int:
    tx_output_types = [get_address_type(addr_str) for addr_str in tx_output_addr_strs]

    (non_witness_estimate, witness_estimate) = estimate_tx_size(
        tx_inputs_count, tx_output_types
    )
    vbytes = non_witness_estimate + witness_estimate / 4
    return math.ceil(sats_per_vbyte * vbytes)


def estimate_tx_size(
    tx_inputs_count: int,
    tx_output_types: List[AddressType],
) -> Tuple[int, int]:
    """
    p2wpkh input, non witness size:

    Fixed bytes:
      Version: 4; Input count, Output count: 2; Locktime: 4
      4 + 2 + 4 = 10
    Each input:
      pre_tx_id: 32; pre_tx_index: 4; script_sig: 1 (segwit); sequence: 4
      32 + 4 + 1 + 4 = 41
    Each output:
      Amount: 8;
      a> to p2wpkh:
        script_pub_size, OP_0, OP_PUSHBYTES: 3; script_pub: 20
        8 + 3 + 20 = 31
      b> to p2wsh:
        script_pub_size, OP_0, OP_PUSHBYTES: 3; script_pub: 32
        8 + 3 + 32 = 43
      c> to p2sh:
        script_pub_size, OP_HASH160, OP_PUSHBYTES, OP_EQUAL: 4; script_pub: 20
        8 + 4 + 20 = 32
    """
    TX_OUTPUT_SIZE = {
        AddressType.WPKH: 31,
        AddressType.WSH: 43,
        AddressType.SH: 32,
    }
    non_witness_estimate = 10 + tx_inputs_count * 41
    for script_type in tx_output_types:
        non_witness_estimate += TX_OUTPUT_SIZE[script_type]

    """
    p2wpkh input, witness size:

    Fixed bytes:
      Segwit marker and flag: 2 bytes
    Each tx_input:
      a> from p2wpkh:
        witness_elements_count: 1; sig_length: 1; sig: 72; pubkey_length: 1; pubkey: 33;
        1 + 1 + 72 + 1 + 33 = 108 bytes
    """
    witness_estimate = 2 + tx_inputs_count * 108
    return (non_witness_estimate, witness_estimate)
