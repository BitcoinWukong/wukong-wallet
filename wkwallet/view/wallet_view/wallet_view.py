from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDTextButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.spinner import MDSpinner
from model.exchange_rate_manager import exchange_rate_manager, toggle_currency
from utils import export_labels_to_file, import_labels_from_file, limit_length
from view.wallet_view.wallet_addresses_tab import WalletAddressesTab
from view.wallet_view.wallet_coins_tab import WalletCoinsTab
from view.wallet_view.wallet_txs_tab import WalletTxsTab
from wallet import Wallet
from wallet_manager import WalletsObserver, wallet_manager

Builder.load_file("view/wallet_view/wallet_view.kv")


class WalletView(Screen, WalletsObserver):
    wallet: Wallet = ObjectProperty()
    manager = ObjectProperty()

    wallet_name_label: MDLabel = ObjectProperty()
    balance_button: MDTextButton = ObjectProperty()
    refresh_spinner: MDSpinner = ObjectProperty()

    coins_tab: WalletCoinsTab = ObjectProperty()
    addresses_tab: WalletAddressesTab = ObjectProperty()
    txs_tab: WalletTxsTab = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        menu_items = [
            {
                "text": "Refresh",
                "height": dp(56),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_refresh(),
            },
            {
                "text": "Edit Wallet",
                "height": dp(56),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_show_edit_wallet(),
            },
            {
                "text": "Toggle FB",
                "height": dp(60),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_toggle_fb(),
            },
            {
                "text": "Export Labels",
                "height": dp(60),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_export_labels(),
            },
            {
                "text": "Import Labels",
                "height": dp(60),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_import_labels(),
            },
        ]
        self.menu = MDDropdownMenu(
            background_color="e0ffff",
            caller=self.ids.dots_vertical_button,
            items=menu_items,
            width_mult=3,
        )

    def set_wallet(self, wallet: Wallet):
        self.wallet = wallet
        Clock.schedule_once(lambda dt: self.update_ui(), 0.3)

    def on_enter(self, *args):
        wallet_manager().register_observer(self)
        self.update_ui()
        return super().on_enter(*args)

    def on_leave(self, *args):
        wallet_manager().deregister_observer(self)
        return super().on_leave(*args)

    def on_balance_updated(self):
        pass

    def press_vertical_dots(self):
        self.menu.open()

    def press_refresh(self):
        def start_refresh():
            self.menu.dismiss()
            if wallet_manager().is_refreshing:
                return
            self.refresh()

        Clock.schedule_once(lambda dt: start_refresh(), 0.15)

    def refresh(self):
        self.refresh_spinner.active = True
        self.ids.dots_vertical_button.disabled = True
        wallet_manager().refresh(target_wallets=[self.wallet])

    def on_tx_summaries_updated(self, refreshing_wallets):
        self.update_ui()

    @mainthread
    def update_ui(self) -> None:
        MAX_WALLET_LABEL_LENGTH = 12

        self.refresh_spinner.active = wallet_manager().is_refreshing
        self.ids.dots_vertical_button.disabled = wallet_manager().is_refreshing
        self.wallet_name_label.text = limit_length(
            self.wallet.wallet_title(), MAX_WALLET_LABEL_LENGTH
        )
        self.update_balance()

        self.coins_tab.update_ui()
        self.addresses_tab.update_ui()
        self.txs_tab.update_ui()

    def on_press_balance_button(self):
        self.wallet.data.currency = toggle_currency(self.wallet.data.currency)
        self.wallet.data.save()

        self.update_balance()
        self.coins_tab.update_ui()
        self.addresses_tab.update_ui()
        self.txs_tab.update_ui()

    def update_balance(self):
        self.balance_button.text = exchange_rate_manager.format_balance(
            self.wallet.total_balance,
            self.wallet.data.currency,
        )

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = self.manager.main_view.name
        self.menu.dismiss()

    def press_show_edit_wallet(self):
        def show_edit_wallet():
            from kivy.uix.screenmanager import CardTransition

            self.menu.dismiss()
            self.manager.transition = CardTransition()
            self.manager.transition.duration = 0.2
            self.manager.transition.direction = "up"
            self.manager.transition.mode = "push"
            self.manager.edit_wallet_view.set_wallet(self.wallet)
            self.manager.current = self.manager.edit_wallet_view.name

        Clock.schedule_once(lambda dt: show_edit_wallet(), 0.15)

    def press_toggle_fb(self):
        def toggle_fb():
            self.menu.dismiss()
            is_fb_enabled = not self.wallet.data.has_fidelity_bonds
            self.wallet.enable_disable_fidelity_bonds(is_fb_enabled)
            self.refresh()

        Clock.schedule_once(lambda dt: toggle_fb(), 0.15)

    def press_export_labels(self):
        def export_labels():
            self.menu.dismiss()
            export_labels_to_file(label_lines=self.wallet.export_labels())

        Clock.schedule_once(lambda dt: export_labels(), 0.15)

    def press_import_labels(self):
        def import_labels():
            self.menu.dismiss()
            import_labels_from_file(target_wallet_data=self.wallet.data)

        Clock.schedule_once(lambda dt: import_labels(), 0.15)
