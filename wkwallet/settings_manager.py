import os
import sys

from kivy.utils import platform


class SettingsManager:
    def __init__(self) -> None:
        # Config the settings_file_path base on the platform.
        if platform == "android":
            from android.storage import app_storage_path  # type: ignore

            self._app_storage_directory_path = app_storage_path()
        elif platform == "linux" or platform == "macosx":
            self._app_storage_directory_path = os.path.join(
                os.path.expanduser("~"), ".wkwallet"
            )
            if not os.path.exists(self._app_storage_directory_path):
                os.makedirs(self._app_storage_directory_path)
        else:
            sys.exit(f"Platform {platform} is not supported yet.")
        self._settings_file_path = os.path.join(
            self._app_storage_directory_path, "settings.cfg"
        )

        # Init settings
        self.server_ip = ""
        self.currency = "sat"

        # Load config from the settings file.
        self.load_settings_config()

    @property
    def app_storage_directory_path(self):
        return self._app_storage_directory_path

    def load_settings_config(self):
        if not os.path.exists(self._settings_file_path):
            return
        settings_file = open(self._settings_file_path, "r")

        # Server IP
        self.server_ip = settings_file.readline()
        if self.server_ip:
            self.server_ip = self.server_ip.strip()
        # Prefered currency
        self.currency = settings_file.readline()
        if self.currency:
            self.currency = self.currency.strip()
        else:
            self.currency = "sat"

    def save_config(self):
        settings_file = open(self._settings_file_path, "w")
        settings_file.write(self.server_ip + "\n")
        settings_file.write(self.currency + "\n")
        settings_file.close()


settings_manager = SettingsManager()
