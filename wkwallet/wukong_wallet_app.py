from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivymd.app import MDApp
from view.add_wallet_view.add_wallet_view import AddWalletView
from view.create_tx_view import CreateTxView
from view.edit_wallet_view import EditWalletView
from view.main_view import MainView
from view.scan_qr_code_view import ScanQRCodeView
from view.select_addresses_view import SelectAddressesView
from view.send_bitcoin_view import SendBitcoinView
from view.settings_view import SettingsView
from view.app_log_view import AppLogView
from view.wallet_view.wallet_view import WalletView


class RootViewManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_view = MainView(name="main_view")
        self.settings_view = SettingsView(name="settings_view")
        self.app_log_view = AppLogView(name="app_log_view")
        self.edit_wallet_view = EditWalletView(name="edit_wallet_view")
        self.add_wallet_view = AddWalletView(name="add_wallet_view")
        self.wallet_view = WalletView(name="wallet_view")
        self.scan_qr_code_view = ScanQRCodeView(name="scan_qr_code_view")
        self.select_addresses_view = SelectAddressesView(name="select_addresses_view")
        self.send_bitcoin_view = SendBitcoinView(name="send_bitcoin_view")
        self.create_tx_view = CreateTxView(name="create_tx_view")

        self.settings_view.main_view = self.main_view
        self.main_view.register_connect_callback(
            self.settings_view.update_connection_status
        )
        self.add_widget(self.main_view)
        self.add_widget(self.settings_view)
        self.add_widget(self.app_log_view)
        self.add_widget(self.edit_wallet_view)
        self.add_widget(self.add_wallet_view)
        self.add_widget(self.wallet_view)
        self.add_widget(self.scan_qr_code_view)
        self.add_widget(self.select_addresses_view)
        self.add_widget(self.send_bitcoin_view)
        self.add_widget(self.create_tx_view)
        self.current = self.main_view.name
        Window.bind(on_keyboard=self.Android_back_click)

    def Android_back_click(self, _, key, *largs):
        if key == 27:
            if self.current_screen != self.main_view:
                self.current_screen.back()
                return True


class WukongWalletApp(MDApp):
    def build(self):
        # Set the status bar and nav bar color on Android.
        status_bar_color = "#FFFFFF"
        nav_bar_color = "#FFFFFF"
        if platform == "android":
            from android.runnable import run_on_ui_thread  # type: ignore
            from jnius import autoclass

            @run_on_ui_thread
            def set_status_nav_bar_color():
                Color = autoclass("android.graphics.Color")
                WindowManager = autoclass("android.view.WindowManager$LayoutParams")
                activity = autoclass("org.kivy.android.PythonActivity").mActivity

                window = activity.getWindow()
                window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
                window.setStatusBarColor(Color.parseColor(status_bar_color))
                window.setNavigationBarColor(Color.parseColor(nav_bar_color))

                view = window.getDecorView()
                view.setSystemUiVisibility(
                    view.getSystemUiVisibility()
                    | view.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                    | view.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
                )

            Clock.schedule_once(lambda dt: set_status_nav_bar_color())

        # RootViewManager is the root widget of the app.
        return RootViewManager()
