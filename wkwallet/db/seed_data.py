from model.crypt_utils import mnemonic_to_root_key
from peewee import CharField

from .base_model import BaseModel


class SeedData(BaseModel):
    # TODO: Encrypt mnemonic and passphrase
    mnemonic = CharField()
    passphrase = CharField(null=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__root_key = mnemonic_to_root_key(self.mnemonic)

    @property
    def root_key(self):
        return self.__root_key
