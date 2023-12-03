from pycoin.symbols.btc import network as BTC


def bytes_to_hex(bytes):
    return "".join(format(x, "02x") for x in bytes)


class Key:
    @classmethod
    def from_str(cls, key_str: str):
        internal_key = BTC.parse(key_str)
        if not internal_key:
            return None
        return cls(internal_key)

    def __init__(self, internal_key) -> None:
        self.internal_key = internal_key

    def subkey_for_path(self, path: str) -> "Key":
        internal_subkey = self.internal_key.subkey_for_path(path)
        return Key(internal_subkey)

    @property
    def hex(self) -> str:
        if self.is_private():
            return self.internal_key.wif()
        else:
            return bytes_to_hex(self.internal_key.sec())

    def is_private(self) -> bool:
        return self.internal_key.is_private()
