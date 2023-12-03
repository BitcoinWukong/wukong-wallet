import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "connectrum"))


import logging

from bitcoin.core.key import use_libsecp256k1_for_signing
from db.database_repo import DatabaseRepo
from kivy.core.window import Window
from kivy.logger import LOG_LEVELS, ColoredFormatter, Logger
from kivy.utils import platform
from settings_manager import settings_manager
from wukong_wallet_app import WukongWalletApp

main_db_repo = None


def initialize():
    global main_db_repo

    # Available logging levels: trace, debug, info, warning, error, critical.
    Logger.setLevel(LOG_LEVELS["info"])
    logging.Formatter.default_msec_format = "%s.%03d"
    Logger.handlers[1].setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    Logger.handlers[2].setFormatter(
        ColoredFormatter("[%(levelname)-18s] %(asctime)s %(message)s")
    )

    # Use secp256k1
    use_libsecp256k1_for_signing(True)

    # Initialize DB
    db_file_path = settings_manager.app_storage_directory_path + "/wk_wallet.db"
    main_db_repo = DatabaseRepo(db_file_path, use_queued_db=True)


if __name__ == "__main__":
    initialize()

    if platform == "linux":
        # According to the doc, 1 inch is supposetd to have 160 points
        # But with trial and error, at least on Pixel 6 Pro, 1 inch somehow
        # has 146.5 points.
        #
        # status_bar_height: 24dp
        # navigation_bar_height: 48dp
        # 24dp + 48dp = 72dp
        #
        # Pixel 6 Pro: 1440p x 3120p, 512ppi
        # 1440p / 512 ppi * 146.5 = 412
        # 3120p / 512 ppi * 146.5 = 893
        # 893 - 72 = 821
        Window.size = (412, 821)
        Window.top = 100
        Window.left = 2800
    elif platform == "macosx":
        Window.size = (412, 821)
        Window.top = 100
        Window.left = 1000

    WukongWalletApp().run()
