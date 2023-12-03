from peewee import CharField, ForeignKeyField, IntegerField

from .account_data import AccountData
from .base_model import BaseModel


class ChainData(BaseModel):
    account = ForeignKeyField(AccountData, backref="chains", on_delete="CASCADE")

    chain_index = IntegerField()
    script_type_name = CharField()

    first_unused_index = IntegerField(default=0)
