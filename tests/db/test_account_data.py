import unittest
from typing import Optional

from wkwallet.db.database_repo import DB_LOCATION_MEMORY, DatabaseRepo


class AccountDataUnitTest(unittest.TestCase):
    zpub_str = "zpub6qSqRUnhGDST2CweecVFEEfzHHFHPiKLqKg9iTtXsAk1AF7PyH75wgEGyxBRYicMhiBhpZPWR1fEShbnRhBbu8kiHrbZiv8n5qUQbd5T7km"

    def setUp(self) -> None:
        self.test_repo: Optional[DatabaseRepo] = DatabaseRepo(DB_LOCATION_MEMORY)

    def tearDown(self) -> None:
        self.test_repo = None

    def test_unable_to_create_account_data_without_valid_wallet_data(self):
        wallet_data = self.test_repo.add_wallet()
        # Before saving wallet_data, it has no valid id, and can not be used to
        # create new account_data
        with self.assertRaises(Exception):
            self.test_repo.add_account(
                wallet_data=wallet_data,
                account_index=0,
                xpub=self.zpub_str,
            )

    def create_wallet_data_and_account_data(self):
        self.wallet_data = self.test_repo.add_wallet()
        self.test_repo.commit()
        self.account_data = self.test_repo.add_account(
            wallet_data=self.wallet_data,
            account_index=0,
            xpub=self.zpub_str,
        )
        self.test_repo.commit()

    def test_create_account_data(self):
        self.create_wallet_data_and_account_data()

        wallets_in_db = self.test_repo.get_wallets()
        self.assertEqual(len(wallets_in_db), 1)
        self.assertEqual(wallets_in_db[0], self.wallet_data)

        accounts_in_db = self.test_repo.get_accounts()
        self.assertEqual(len(accounts_in_db), 1)
        self.assertEqual(accounts_in_db[0], self.account_data)
        self.assertEqual(accounts_in_db[0].xpub, self.zpub_str)

    def test_delete_wallet_data_also_deletes_account_data(self):
        self.create_wallet_data_and_account_data()

        # Remove wallet
        self.test_repo.delete(self.wallet_data)
        # Before committing, the wallet is still there
        self.assertEqual(len(self.test_repo.get_wallets()), 1)

        # Assert both the wallet_data and the account_data are removed from db
        self.test_repo.commit()
        self.assertEqual(len(self.test_repo.get_wallets()), 0)
        self.assertEqual(len(self.test_repo.get_accounts()), 0)

    def test_delete_account_data_does_not_delete_wallet_data(self):
        self.create_wallet_data_and_account_data()

        # Remove account
        self.test_repo.delete(self.account_data)
        # Before committing, the account is still there
        self.assertEqual(len(self.test_repo.get_accounts()), 1)

        # Assert only the account_data has been removed from db
        self.test_repo.commit()
        self.assertEqual(len(self.test_repo.get_wallets()), 1)
        self.assertEqual(len(self.test_repo.get_accounts()), 0)
