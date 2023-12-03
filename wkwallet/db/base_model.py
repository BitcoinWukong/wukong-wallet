from peewee import Database, DatabaseProxy, Model

_main_database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = _main_database_proxy


def setup_database_proxy(database: Database):
    _main_database_proxy.initialize(database)
