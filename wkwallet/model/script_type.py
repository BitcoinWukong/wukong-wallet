import hashlib
from abc import abstractmethod

import pycoin
from pycoin.symbols.btc import network as BTC

from .fidelity_bond import address_index_to_locktime, time_lock_script
from .crypt_utils import bytes_to_hex, script_to_ES_hash


class ScriptType:
    class BaseScriptType:
        def __init__(self, key: pycoin.key.Key.Key, address_index=None) -> None:
            self.key = key
            self.address_index = address_index

        @abstractmethod
        def address(self):
            pass

        @abstractmethod
        def script(self):
            pass

        # Electrum Server protocol script hash for querying on Electrum Server.
        def ES_hash(self):
            return script_to_ES_hash(self.script())

        @classmethod
        def derivation_path(cls):
            pass

        @classmethod
        def script_type_name(cls):
            return "BaseScriptType"

    class PKH(BaseScriptType):
        def address(self):
            return BTC.address.for_p2pkh(self.key.hash160())

        @classmethod
        def derivation_path(cls):
            return "44p/0p"

        @classmethod
        def script_type_name(cls):
            return "PKH"

    class SH_WPKH(BaseScriptType):
        def address(self):
            wpkh_script = BTC.contract.for_p2pkh_wit(self.key.hash160())
            return BTC.address.for_p2s(wpkh_script)

        @classmethod
        def derivation_path(cls):
            return "49p/0p"

        @classmethod
        def script_type_name(cls):
            return "SH_WPKH"

    class WPKH(BaseScriptType):
        def __init__(self, key: pycoin.key.Key.Key, address_index=None) -> None:
            super().__init__(key, address_index)
            self.key_hash = None

        def address(self):
            return BTC.address.for_p2pkh_wit(self._key_hash())

        def script(self):
            return BTC.contract.for_p2pkh_wit(self._key_hash())

        @classmethod
        def derivation_path(cls):
            return "84p/0p"

        @classmethod
        def script_type_name(cls):
            return "WPKH"

        def _key_hash(self):
            if not self.key_hash:
                self.key_hash = self.key.hash160()
            return self.key_hash

    class WSH(BaseScriptType):
        def __init__(self, key: pycoin.key.Key.Key, address_index=None) -> None:
            super().__init__(key, address_index)
            self.key_hash = None

        def address(self):
            return BTC.address.for_p2sh_wit(self._script_hash())

        def script(self):
            return BTC.contract.for_p2sh_wit(self._script_hash())

        @classmethod
        def script_type_name(cls):
            return "WSH"

        def _script_hash(self):
            if not self.key_hash:
                self.key_hash = self.key.hash160()
            return self.key_hash

    class WSH_FB(BaseScriptType):
        def __init__(self, key: pycoin.key.Key.Key, address_index=None) -> None:
            super().__init__(key, address_index)
            self.time_lock_script_hash = None

        def address(self):
            return BTC.address.for_p2sh_wit(self._time_lock_script_hash())

        def script(self):
            return BTC.contract.for_p2sh_wit(self._time_lock_script_hash())

        @classmethod
        def derivation_path(cls):
            return "84p/0p/0p/2"

        @classmethod
        def script_type_name(cls):
            return "WSH_FB"

        def _time_lock_script_hash(self):
            if not self.time_lock_script_hash:
                time_lock_script = self._time_lock_script()
                self.time_lock_script_hash = hashlib.sha256(time_lock_script).digest()
            return self.time_lock_script_hash

        def _time_lock_script(self):
            locktime = address_index_to_locktime(self.address_index)
            pubkey_hex = bytes_to_hex(self.key.sec())
            return time_lock_script(locktime, pubkey_hex)


# PK = "m/44'/0'/0'"
# PKH = "m/44'/0'/0'"
# SH = "m/45'"
# SH_WPKH = "m/49'/0'/0'"
# SH_WSH = "m/48'/0'/0'/1'"
# WPKH = "m/84'/0'/0'"
# WSH_FB = "m/84'/0'/0'/2"
# WSH = "m/48'/0'/0'/2'"
# TR = "m/86'/0'/0'"

script_types = {
    "PKH": ScriptType.PKH,
    "SH_WPKH": ScriptType.SH_WPKH,
    "WPKH": ScriptType.WPKH,
    "WSH_FB": ScriptType.WSH_FB,
    "WSH": ScriptType.WSH,
}
