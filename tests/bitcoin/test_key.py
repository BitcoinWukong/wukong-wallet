import unittest

from wkwallet.bitcoin.key import Key


class KeyUnitTest(unittest.TestCase):
    yprv_str = "yprvAKK7gixAFJLhzvFvyWy2CRFx5GQC4gpe4nQCEHMCCFUphm1YwPo4Gko38pCTUijNb8Jw7e2w4UHDZN6qER2E3QY4MdimUkyxj4FrV6oABXp"
    yprv_hex = "L2rJZ5CoqmuL1W9Es5WdY35eWZPHepFz8q3RFLMRjBv5fYjAfoJA"
    ypub_str = "ypub6YJU6EV45fu1DQLQ5YW2ZZCgdJEgU9YVS1Ko2fkokb1oaZLhUw7JpZ7Wz48voFZ9YLSKEukvEUMyGdn4HY3dyS7dYPuYHYTSuENMUoHmrsH"
    ypub_hex = "02184ac43ccf50b85f19cfffe3c8232f686a5b53ab097bc54936fce207712f7679"

    zprv_str = "zprvAcTV1yFoRqt9oisBYaxEs6jFjFQnzFbVU6kYv5UvJqD2HSnFRjnqPsuo8fmx7RE8Yz5bcAeFKECbpYnkCZgBwHPgbXgo2JdkhCpbEPQcWx9"
    zprv_hex = "L2nzJukVV9bXZCBzKP9x8B6CgEr4D6fXmPb9AcSWYVaRj1EfASk8"
    zpub_str = "zpub6qSqRUnhGDST2CweecVFEEfzHHFHPiKLqKg9iTtXsAk1AF7PyH75wgEGyxBRYicMhiBhpZPWR1fEShbnRhBbu8kiHrbZiv8n5qUQbd5T7km"
    zpub_hex = "035b4a5d4f079f64847573075521115cf55f59f70eba763c5cf46992cc743da23b"

    def test_yprv_key_parse(self):
        yprv_key = Key.from_str(self.yprv_str)
        self.assertIsNotNone(yprv_key)
        self.assertEqual(yprv_key.hex, self.yprv_hex)
        self.assertTrue(yprv_key.is_private())

    def test_ypub_key_parse(self):
        ypub_key = Key.from_str(self.ypub_str)
        self.assertIsNotNone(ypub_key)
        self.assertEqual(ypub_key.hex, self.ypub_hex)
        self.assertFalse(ypub_key.is_private())

    def test_zprv_key_parse(self):
        zprv_key = Key.from_str(self.zprv_str)
        self.assertIsNotNone(zprv_key)
        self.assertEqual(zprv_key.hex, self.zprv_hex)
        self.assertTrue(zprv_key.is_private())

    def test_zpub_key_parse(self):
        zpub_key = Key.from_str(self.zpub_str)
        self.assertIsNotNone(zpub_key)
        self.assertEqual(zpub_key.hex, self.zpub_hex)
        self.assertFalse(zpub_key.is_private())

    def test_subkey_of_ypub(self):
        expected_pubkey_hex = (
            "02eaa1f167fa59be67836d667e3cdf4b2a26fe1f3f2535c89cd96f58c9cd72af70"
        )
        ypub_key = Key.from_str(self.ypub_str)
        pubkey_0_0 = ypub_key.subkey_for_path("0/0")
        self.assertIsInstance(pubkey_0_0, Key)
        self.assertEqual(pubkey_0_0.hex, expected_pubkey_hex)

    def test_invalid_key_parse(self):
        invalid_key_str = "abcdefg"
        self.assertIsNone(Key.from_str(invalid_key_str))
