import unittest
from wkwallet.model.script_type import ScriptType
from pycoin.symbols.btc import network as BTC

class ScriptTypeUnitTest(unittest.TestCase):
    mnemonic = 'east vintage light claw survey snake dawn kiwi vacant wheat phrase flavor'

    def setUp(self):
        ypub = 'ypub6YJU6EV45fu1DQLQ5YW2ZZCgdJEgU9YVS1Ko2fkokb1oaZLhUw7JpZ7Wz48voFZ9YLSKEukvEUMyGdn4HY3dyS7dYPuYHYTSuENMUoHmrsH'
        zpub = 'zpub6qSqRUnhGDST2CweecVFEEfzHHFHPiKLqKg9iTtXsAk1AF7PyH75wgEGyxBRYicMhiBhpZPWR1fEShbnRhBbu8kiHrbZiv8n5qUQbd5T7km'

        self.ypub_key = BTC.parse(ypub)
        self.zpub_key = BTC.parse(zpub)

    def test_sh_wpkh_address(self):
        pubkey = self.ypub_key.subkey_for_path('0/0')
        self.assertEqual(
            ScriptType.SH_WPKH(pubkey).address(),
            '3JAKVZztstukAHcs35qhiktrsxAMFxfLXP'
        )

    def test_wpkh_address_0_0(self):
        pubkey = self.zpub_key.subkey_for_path('0/0')
        self.assertEqual(
            ScriptType.WPKH(pubkey).address(),
            'bc1quv97d3679z2t5z5y2ttafkru7d6y4063jpxkfx'
        )

    def test_wpkh_address_1_0(self):
        pubkey = self.zpub_key.subkey_for_path('1/0')
        self.assertEqual(
            ScriptType.WPKH(pubkey).address(),
            'bc1q2gphp6cwuplknfupkehhvyvcs58w84ke3g6n79'
        )

    def test_wpkh_ES_hash_0_0(self):
        pubkey = self.zpub_key.subkey_for_path('0/0')
        self.assertEqual(
            ScriptType.WPKH(pubkey).ES_hash(),
            'b911d7368f26a59580ed26928b32c3a3930904a79fbe5e053224cd5de25c8549'
        )

    def test_wpkh_ES_hash_1_0(self):
        pubkey = self.zpub_key.subkey_for_path('1/0')
        self.assertEqual(
            ScriptType.WPKH(pubkey).ES_hash(),
            'cdf3e95bc71fb2b1b27f53d77e096c75e26daf02c34f79fa4f9fe0d0b6315cfa'
        )

    def test_wsh_fb_address(self):
        pubkey = self.zpub_key.subkey_for_path('2/0')
        self.assertEqual(
            ScriptType.WSH_FB(pubkey, 0).address(),
            'bc1q9cfc52ad8a47tzlyatuxkhsqk2hkzjzdueg75z87g7mvqdgd4uus9upwmm'
        )

    def test_wsh_fb_ES_hash(self):
        pubkey = self.zpub_key.subkey_for_path('2/0')
        self.assertEqual(
            ScriptType.WSH_FB(pubkey, 0).ES_hash(),
            'eb7b75cdb90a375cb78c0efb0978de9e92686dd65ead244de9e8cc2f603e0567'
        )
