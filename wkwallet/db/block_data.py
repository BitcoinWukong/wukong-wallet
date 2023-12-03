from peewee import CharField, DateTimeField, IntegerField

from .base_model import BaseModel


class BlockData(BaseModel):
    height = IntegerField(primary_key=True)
    header_hex = CharField(null=True)
    timestamp = DateTimeField(null=True)
