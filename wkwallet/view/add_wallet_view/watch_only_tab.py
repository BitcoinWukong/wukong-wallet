from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.textfield import MDTextField
from view.scan_qr_code_view import QRScanObserver, ScanQRCodeView
from wallet_manager import wallet_manager


class WatchOnlyTab(MDFloatLayout, MDTabsBase, QRScanObserver):
    manager: ScreenManager = ObjectProperty()
    wallet_accounts_list: MDBoxLayout = ObjectProperty()

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = "main_view"

    def reset(self):
        self.account_xpub_inputs = []
        self.wallet_accounts_list.clear_widgets()
        self.add_account()

    def press_scan(self) -> None:
        scan_qr_code_view: ScanQRCodeView = self.manager.scan_qr_code_view
        scan_qr_code_view.observer = self
        scan_qr_code_view.back_view_name = "add_wallet_view"
        self.manager.add_wallet_view.should_reset = False
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = scan_qr_code_view.name

    def on_scan(self, scan_str):
        self.account_xpub_inputs[-1].text = scan_str

    def press_add_account(self):
        self.add_account()

    def add_account(self):
        account_xpub_text_field = MDTextField()
        account_xpub_text_field.hint_text = (
            f"Xpub for Account {len(self.account_xpub_inputs)}"
        )
        account_xpub_text_field.multiline = True
        self.account_xpub_inputs.append(account_xpub_text_field)
        self.wallet_accounts_list.add_widget(account_xpub_text_field)

    def press_add(self):
        xpubs = []
        for xpub_input in self.account_xpub_inputs:
            xpubs.append(xpub_input.text.strip())

        if not wallet_manager().create_watch_only_wallet(xpubs):
            # TODO: Give an error message about invalid xpub
            return

        self.back()
        # TODO: Only refresh the newly added wallet.
        Clock.schedule_once(lambda dt: self.manager.main_view.refresh(), 0.5)
