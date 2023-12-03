import unittest

from wkwallet.model.script_type import ScriptType
from wkwallet.model.wallet_account import WalletAccount


class WalletAccountUnitTest(unittest.TestCase):
    mnemonic = 'east vintage light claw survey snake dawn kiwi vacant wheat phrase flavor'

#     def setUp(self):
#         ypub_0 = "ypub6YJU6EV45fu1DQLQ5YW2ZZCgdJEgU9YVS1Ko2fkokb1oaZLhUw7JpZ7Wz48voFZ9YLSKEukvEUMyGdn4HY3dyS7dYPuYHYTSuENMUoHmrsH"

#         zpub_0 = "zpub6qSqRUnhGDST2CweecVFEEfzHHFHPiKLqKg9iTtXsAk1AF7PyH75wgEGyxBRYicMhiBhpZPWR1fEShbnRhBbu8kiHrbZiv8n5qUQbd5T7km"
#         zpub_1 = "zpub6qSqRUnhGDST5dPpapMGpP4s56yKkuv64KJbD7zjbnNLRBENzUJuri4zyR26fvt1nYTRmuznjZJAgdR7hpD5SSac2JRsD1nsKrn5bUPhVkY"
#         zpub_2 = "zpub6qSqRUnhGDST7YAqnsnN8G7hiGdKJARaQmU4fMQMrYnqn7F97XCWGxBN1Jr1nehyVDCfZ3soDahXAvksRVricA2bGC81X8wJU3Yb2114HJQ"
#         zpub_3 = "zpub6qSqRUnhGDSTABL4dE1GLScTXJ3rxSYfGdLXU4P8jwPVe7VAWheK5kV8CiC21v33m1as16iWfQV42v19RZMQ7UPmnkn9G1t2wEvrF3LWGnq"
#         zpub_4 = "zpub6qSqRUnhGDSTCsr7J2zLtitdqAEBgCktmEbMG88dw8RmZpMW9QAdYTZ3Z8BKJGGaNfUFiBrLevqaZbGQQxHbRgEkhV1X91g3eQR2ucSabCh"

#         self.sh_wpkh_mix_depth_0 = WalletAccount.create_account(
#             ypub_0,
#             {
#                 0: ScriptType.SH_WPKH,
#                 1: ScriptType.SH_WPKH,
#             },
#         )

#         self.wpkh_mix_depth_0 = WalletAccount.create_account(
#             zpub_0,
#             {
#                 0: ScriptType.WPKH,
#                 1: ScriptType.WPKH,
#                 2: ScriptType.WSH_FB,
#             },
#         )

#         self.wpkh_mix_depth_1 = WalletAccount.create_account(
#             zpub_1,
#             {
#                 0: ScriptType.WPKH,
#                 1: ScriptType.WPKH,
#             },
#         )

#     def tearDown(self) -> None:
#         self.sh_wpkh_mix_depth_0.delete_instance()
#         self.wpkh_mix_depth_0.delete_instance()
#         self.wpkh_mix_depth_1.delete_instance()

#     def test_sh_wpkh_address(self):
#         self.assertEqual(
#             self.sh_wpkh_mix_depth_0.address_for_path("0/0"),
#             "3JAKVZztstukAHcs35qhiktrsxAMFxfLXP",
#         )

#     def test_md0_address_1(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_0.address_for_path("0/0"),
#             "bc1quv97d3679z2t5z5y2ttafkru7d6y4063jpxkfx",
#         )

#     def test_md0_address_2(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_0.address_for_path("1/0"),
#             "bc1q2gphp6cwuplknfupkehhvyvcs58w84ke3g6n79",
#         )

#     def test_md1_address_1(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_1.address_for_path("0/0"),
#             "bc1qwlye8chenrtc8eqfw2shkmr9m205xcwcy0cajg",
#         )

#     def test_md1_address_2(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_1.address_for_path("1/0"),
#             "bc1qrr6hzj0x8skems6nvjnj0yadn02unkjrrgl6pl",
#         )

#     def test_md0_ES_hash_1(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_0.ES_hash_for_path("0/0"),
#             "b911d7368f26a59580ed26928b32c3a3930904a79fbe5e053224cd5de25c8549",
#         )

#     def test_md0_ES_hash_2(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_0.ES_hash_for_path("1/0"),
#             "cdf3e95bc71fb2b1b27f53d77e096c75e26daf02c34f79fa4f9fe0d0b6315cfa",
#         )

#     def test_md0_fb_address(self):
#         self.assertEqual(
#             self.wpkh_mix_depth_0.address_for_path("2/0"),
#             "bc1q9cfc52ad8a47tzlyatuxkhsqk2hkzjzdueg75z87g7mvqdgd4uus9upwmm",
#         )

#     def test_md0_invalid_chain_index(self):
#         self.assertIsNone(self.wpkh_mix_depth_0.address_for_path("3/0"))

#     def test_md1_invalid_chain_index(self):
#         self.assertIsNone(self.wpkh_mix_depth_1.address_for_path("2/0"))
