import unittest
from typing import Optional

from wkwallet.db.database_repo import DB_LOCATION_MEMORY, DatabaseRepo
from wkwallet.db.wallet_data import WalletData


class WalletDataUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_repo: Optional[DatabaseRepo] = DatabaseRepo(DB_LOCATION_MEMORY)

    def tearDown(self) -> None:
        self.test_repo = None

    def test_create_wallet_data(self):
        # There should be no wallet at the beginning
        self.assertEqual(len(self.test_repo.get_wallets()), 0)

        wallet_data = self.test_repo.add_wallet()
        self.assertIsInstance(wallet_data, WalletData)
        # The wallet isn't saved to db until commit is called
        self.assertEqual(len(self.test_repo.get_wallets()), 0)

        # After commit, the wallet should be in the db
        self.test_repo.commit()
        self.assertEqual(len(self.test_repo.get_wallets()), 1)

    def test_update_wallet_data_name(self):
        name1 = "name1"
        name2 = "name2"

        wallet_data = self.test_repo.add_wallet()
        wallet_data.name = name1
        self.test_repo.commit()
        wallet_data_in_db = self.test_repo.get_wallets()[0]
        self.assertEqual(wallet_data_in_db.name, name1)

        wallet_data.name = name2
        self.test_repo.update(wallet_data)
        self.test_repo.commit()
        wallet_data_in_db = self.test_repo.get_wallets()[0]
        self.assertEqual(wallet_data_in_db.name, name2)
