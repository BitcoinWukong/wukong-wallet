import unittest

from wkwallet.model.script_type import ScriptType

# class WalletUnitTest(unittest.TestCase):
#     def setUp(self):
#         mnemonic = 'east vintage light claw survey snake dawn kiwi vacant wheat phrase flavor'
#         zpub_0 = 'zpub6qSqRUnhGDST2CweecVFEEfzHHFHPiKLqKg9iTtXsAk1AF7PyH75wgEGyxBRYicMhiBhpZPWR1fEShbnRhBbu8kiHrbZiv8n5qUQbd5T7km'
#         zpub_1 = 'zpub6qSqRUnhGDST5dPpapMGpP4s56yKkuv64KJbD7zjbnNLRBENzUJuri4zyR26fvt1nYTRmuznjZJAgdR7hpD5SSac2JRsD1nsKrn5bUPhVkY'
#         zpub_2 = 'zpub6qSqRUnhGDST7YAqnsnN8G7hiGdKJARaQmU4fMQMrYnqn7F97XCWGxBN1Jr1nehyVDCfZ3soDahXAvksRVricA2bGC81X8wJU3Yb2114HJQ'
#         zpub_3 = 'zpub6qSqRUnhGDSTABL4dE1GLScTXJ3rxSYfGdLXU4P8jwPVe7VAWheK5kV8CiC21v33m1as16iWfQV42v19RZMQ7UPmnkn9G1t2wEvrF3LWGnq'
#         zpub_4 = 'zpub6qSqRUnhGDSTCsr7J2zLtitdqAEBgCktmEbMG88dw8RmZpMW9QAdYTZ3Z8BKJGGaNfUFiBrLevqaZbGQQxHbRgEkhV1X91g3eQR2ucSabCh'

#         self.bip44_wallet = create_wallet_from_mnemonic(
#             script_type=ScriptType.PKH,
#             mnemonic=mnemonic,
#         )
#         self.bip84_wallet = create_wallet_from_mnemonic(
#             script_type=ScriptType.WPKH,
#             mnemonic=mnemonic,
#         )

#         self.watch_only_jm_wallet = create_watch_only_jm_wallet(
#             script_type=ScriptType.WPKH,
#             xpubs=
#             [
#                 zpub_0, zpub_1, zpub_2, zpub_3, zpub_4
#             ],
#             has_fidelity_bond = True,
#         )

#     def test_bip44_xpub_derivation(self):
#         xpub = 'xpub6DTcmZkqerWSfMGe49ABZvaHQwtYUgy7FRSbFDf1HtiM3sEqMP42x2msqGsusqYbzqXpd7NpYWFrjg5vhZ4cHqhzpEgCUkEe89XfMAdPfDD'
#         self.assertEqual(
#             self.bip44_wallet.accounts[0].xpub,
#             xpub,
#         )

#     def test_bip44_address(self):
#         self.assertEqual(
#             self.bip44_wallet.accounts[0].address_for_path('0/0'),
#             '18Vfe2ju27hVxqshQPis8jThCD5HWGkvhp'
#         )

#     def test_bip84_xpub_derivation(self):
#         xpub = 'xpub6BnJp9SrxrMVKcZQytuzp4UywLxPWULM16di9g6m79zF43UwTxmxhYuzwYGFYuJWtRx6KcCPVgx8g8NezJMaJfPWZBCiZ6VoYPM7pYjMtyC'
#         self.assertEqual(
#             self.bip84_wallet.accounts[0].xpub,
#             xpub,
#         )

#     def test_bip84_address(self):
#         self.assertEqual(
#             self.bip84_wallet.accounts[0].address_for_path('0/0'),
#             'bc1quv97d3679z2t5z5y2ttafkru7d6y4063jpxkfx'
#         )

#     def test_wpkh_address_for_path_1(self):
#         self.assertEqual(
#             self.watch_only_jm_wallet.accounts[0].address_for_path('0/0'),
#             'bc1quv97d3679z2t5z5y2ttafkru7d6y4063jpxkfx'
#         )

#     def test_wpkh_address_for_path_2(self):
#         self.assertEqual(
#             self.watch_only_jm_wallet.accounts[0].address_for_path('1/0'),
#             'bc1q2gphp6cwuplknfupkehhvyvcs58w84ke3g6n79'
#         )

#     def test_wpkh_address_for_path_3(self):
#         self.assertEqual(
#             self.watch_only_jm_wallet.accounts[1].address_for_path('0/0'),
#             'bc1qwlye8chenrtc8eqfw2shkmr9m205xcwcy0cajg'
#         )

#     def test_wpkh_address_for_path_4(self):
#         self.assertEqual(
#             self.watch_only_jm_wallet.accounts[1].address_for_path('1/0'),
#             'bc1qrr6hzj0x8skems6nvjnj0yadn02unkjrrgl6pl'
#         )

#     def test_wsh_fb_address(self):
#         self.assertEqual(
#             self.watch_only_jm_wallet.accounts[0].address_for_path('2/0'),
#             'bc1q9cfc52ad8a47tzlyatuxkhsqk2hkzjzdueg75z87g7mvqdgd4uus9upwmm'
#         )

#     def test_invalid_chain_index(self):
#         self.assertIsNone(self.watch_only_jm_wallet.accounts[0].address_for_path('3/0'))

#     def test_invalid_chain_index_1(self):
#         self.assertIsNone(self.watch_only_jm_wallet.accounts[1].address_for_path('2/0'))
