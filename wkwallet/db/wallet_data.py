from peewee import BooleanField, CharField, ForeignKeyField, IntegerField

from .base_model import BaseModel
from .seed_data import SeedData

DEFAULT_GAP_LIMIT = 20


class WalletData(BaseModel):
    name = CharField(default="")
    seed_data = ForeignKeyField(SeedData, null=True)

    has_fidelity_bonds = BooleanField(default=False)
    gap_limit = IntegerField(default=DEFAULT_GAP_LIMIT)
    completed_initial_sync = BooleanField(default=False)
    currency = CharField(default="sat")
