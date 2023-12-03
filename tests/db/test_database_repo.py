import os
import tempfile
import unittest

from wkwallet.db.database_repo import DB_LOCATION_MEMORY, DatabaseRepo


def remove_file_if_exist(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


class DatabaseRepoUnitTest(unittest.TestCase):
    def test_creating_in_memory_database_repo(self):
        self.test_repo = DatabaseRepo(DB_LOCATION_MEMORY)
        self.assertTrue(self.test_repo.is_connected())

    def test_creating_on_disk_database_repo(self):
        unit_test_db_path = os.path.join(tempfile.gettempdir(), "unit_test.db")

        # Make sure the db file doesn't exist when starting the test
        remove_file_if_exist(unit_test_db_path)
        self.assertFalse(os.path.isfile(unit_test_db_path))

        # After creating database repo, the db file exists and the connection is open
        self.test_repo = DatabaseRepo(unit_test_db_path)
        self.assertTrue(os.path.isfile(unit_test_db_path))
        self.assertTrue(self.test_repo.is_connected())

        # Cleanup
        remove_file_if_exist(unit_test_db_path)
