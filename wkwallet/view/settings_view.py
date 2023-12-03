from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from settings_manager import settings_manager
from utils import export_labels_to_file, import_labels_from_file
from version import __commit_sha__, __build_type__, __version__, __build_time__
from wallet_manager import wallet_manager

Builder.load_file("view/settings_view.kv")


class SettingsView(Screen):
    server_ip_input = ObjectProperty()
    connection_status_label = ObjectProperty()
    main_view = ObjectProperty()

    def on_pre_enter(self, *args):
        self.refresh()
        return super().on_pre_enter(*args)

    def back(self):
        self.manager.transition.direction = "down"
        self.manager.transition.mode = "pop"
        self.manager.current = self.manager.main_view.name

    def refresh(self):
        self.server_ip_input.text = settings_manager.server_ip
        if __build_type__ == "debug":
            self.ids.app_version_label.text = (
                f"Wukong v{__version__} ({__build_time__}, {__commit_sha__})"
            )
        else:
            self.ids.app_version_label.text = f"Wukong v{__version__}"

    def press_connect(self):
        settings_manager.server_ip = self.server_ip_input.text.strip()
        settings_manager.save_config()
        self.main_view.connect(force_reconnect=True)

    def update_connection_status(self, conn_status):
        self.connection_status_label.text = conn_status

    def press_export_labels(self):
        export_labels_to_file(label_lines=wallet_manager().export_labels())

    def press_import_labels(self):
        import_labels_from_file()
