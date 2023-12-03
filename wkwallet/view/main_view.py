import asyncio
from typing import List

from db.tx_data import TxData
from electrum_client import electrum_client
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDTextButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarListItem
from kivymd.uix.menu import MDDropdownMenu
from model.exchange_rate_manager import exchange_rate_manager, toggle_currency
from settings_manager import settings_manager
from tx_summary_view_model import TxSummaryRow
from utils import limit_length
from view.components.transaction_list_item import MAX_TX_LABEL_LEN
from view.wallet_view.wallet_view import WalletView
from wallet import Wallet
from wallet_manager import WalletsObserver, wallet_manager

Builder.load_file("view/main_view.kv")


class WalletCard(MDCard):
    wallet = ObjectProperty()  # type: Wallet
    title = StringProperty()
    balance = StringProperty()
    manager = ObjectProperty()

    def on_release(self):
        def show_wallet() -> None:
            wallet_view: WalletView = self.manager.wallet_view
            wallet_view.set_wallet(self.wallet)
            self.manager.transition.duration = 0.2
            self.manager.transition.direction = "left"
            self.manager.transition.mode = "push"
            self.manager.current = wallet_view.name

        Clock.schedule_once(lambda dt: show_wallet(), 0.15)


class CreateWalletCard(MDCard):
    manager = ObjectProperty()

    def on_release(self):
        def show_create_wallet():
            self.manager.transition.duration = 0.2
            self.manager.transition.direction = "left"
            self.manager.transition.mode = "push"
            self.manager.current = self.manager.add_wallet_view.name

        Clock.schedule_once(lambda dt: show_create_wallet(), 0.15)


class DepositAddressDialogContent(BoxLayout):
    delta = 0
    wallet = ObjectProperty()  # type: Wallet
    address = StringProperty()
    path = StringProperty()
    main_view = ObjectProperty()  # type: MainView
    pass


class SelectWalletListItem(OneLineAvatarListItem):
    wallet = ObjectProperty()  # type: Wallet
    main_view = ObjectProperty()  # type: MainView

    def on_release(self):
        self.main_view.select_receive_wallet_dialog.dismiss()
        self.main_view.show_address_dialog(self.wallet)


class MainView(Screen, WalletsObserver):
    balance_button: MDTextButton = ObjectProperty()
    refresh_spinner = ObjectProperty()
    receive_button = ObjectProperty()
    tx_history_list = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.wallet_cards = []
        self.connect_callback = None

        menu_items = [
            {
                "text": "Refresh",
                "height": dp(56),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_refresh(),
            },
            {
                "text": "Logs",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_show_logs(),
            },
            {
                "text": "Settings",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.press_show_settings(),
            },
        ]
        self.menu = MDDropdownMenu(
            background_color="e0ffff",
            caller=self.ids.dots_vertical_button,
            items=menu_items,
            width_mult=2,
        )
        self.connect()

    def on_enter(self, *args):
        wallet_manager().register_observer(self)
        self.update_ui()
        return super().on_enter(*args)

    def press_refresh(self):
        def start_refresh():
            self.menu.dismiss()

            if wallet_manager().is_refreshing:
                return
            self.refresh()

        Clock.schedule_once(lambda dt: start_refresh(), 0.15)

    def press_receive(self):
        self.select_receive_wallet_dialog = MDDialog(
            title="Receive in Wallet",
            type="simple",
            items=[
                SelectWalletListItem(
                    text=wallet.wallet_title(), wallet=wallet, main_view=self
                )
                for wallet in wallet_manager().wallets
            ],
        )
        self.select_receive_wallet_dialog.open()

    def show_address_dialog(self, wallet: Wallet):
        address, path = wallet.get_deposit_address()
        self.address_dialog = MDDialog(
            title=f'Receive in "{wallet.wallet_title()}"',
            type="custom",
            content_cls=DepositAddressDialogContent(
                address=address,
                path=path,
                wallet=wallet,
                main_view=self,
            ),
        )
        self.address_dialog.open()

    def register_connect_callback(self, connect_callback):
        self.connect_callback = connect_callback

    def connect(self, force_reconnect=False):
        if not electrum_client.has_server_config() or force_reconnect:
            electrum_client.config_server(settings_manager.server_ip)

        async def connect_async():
            connect_result = await electrum_client.connect_async()
            if connect_result == 0:
                self.refresh()
            if self.connect_callback:
                self.connect_callback(electrum_client.conn_status())

        asyncio.run_coroutine_threadsafe(
            connect_async(),
            electrum_client.loop,
        )

    def press_vertical_dots(self):
        self.menu.open()

    def press_show_settings(self):
        def show_settings():
            from kivy.uix.screenmanager import CardTransition

            self.menu.dismiss()
            self.manager.transition = CardTransition()
            self.manager.transition.duration = 0.2
            self.manager.transition.direction = "up"
            self.manager.transition.mode = "push"
            self.manager.current = self.manager.settings_view.name

        Clock.schedule_once(lambda dt: show_settings(), 0.15)

    def press_show_logs(self):
        def show_logs():
            from kivy.uix.screenmanager import CardTransition

            self.menu.dismiss()
            self.manager.transition = CardTransition()
            self.manager.transition.duration = 0.2
            self.manager.transition.direction = "up"
            self.manager.transition.mode = "push"
            self.manager.current = self.manager.app_log_view.name

        Clock.schedule_once(lambda dt: show_logs(), 0.15)

    @mainthread
    def refresh(self):
        self.balance_button.text = "- sats"
        self.wallet_cards = [
            WalletCard(wallet=wallet, title=wallet.wallet_title(), manager=self.manager)
            for wallet in wallet_manager().wallets
        ]
        self.ids.wallet_cards.clear_widgets()
        for wallet_card in self.wallet_cards:
            self.ids.wallet_cards.add_widget(wallet_card)

        create_wallet_button = CreateWalletCard(manager=self.manager)
        self.ids.wallet_cards.add_widget(create_wallet_button)
        wallet_manager().update_tx_summaries()

        if not wallet_manager().wallets:
            self.receive_button.disabled = True
            self.ids.tx_history_list.data = []
            self.refresh_spinner.active = False
            self.ids.refresh_layout.refresh_done()
            return
        if not electrum_client.has_server_config():
            # TODO: Show an error banner and prompt the user to update server config
            self.ids.refresh_layout.refresh_done()
            return
        if not electrum_client.is_connected():
            self.connect()
            return

        # Fetch the balances from all wallet addresses
        self.refresh_spinner.active = True

        # Refresh wallets.
        wallet_manager().refresh()

    def on_balance_updated(self):
        self.update_toplevel_ui()

    def on_press_balance_button(self):
        settings_manager.currency = toggle_currency(
            settings_manager.currency,
            allow_hidden=False,
        )
        settings_manager.save_config()
        self.update_ui()

    def update_toplevel_ui(self):
        if not wallet_manager().wallets:
            self.balance_button.disabled = True
            self.balance_button.text = " "
        elif all(wallet.is_hidden() for wallet in wallet_manager().wallets):
            self.balance_button.disabled = True
            self.balance_button.text = "all wallets hidden"
        else:
            self.balance_button.disabled = False
            total_balance = sum(
                wallet.total_balance if not wallet.is_hidden() else 0
                for wallet in wallet_manager().wallets
            )
            self.balance_button.text = exchange_rate_manager.format_balance(
                total_balance,
                settings_manager.currency,
            )
        self.refresh_spinner.active = wallet_manager().is_refreshing
        if self.receive_button.disabled:
            self.receive_button.disabled = wallet_manager().is_refreshing

        for wallet_card in self.wallet_cards:
            MAX_WALLET_LABEL_LENGTH = 12

            wallet_card.title = limit_length(
                wallet_card.wallet.wallet_title(), MAX_WALLET_LABEL_LENGTH
            )
            wallet_card.balance = exchange_rate_manager.format_balance(
                wallet_card.wallet.total_balance,
                wallet_card.wallet.data.currency,
            )

    def update_ui(self) -> None:
        self.update_toplevel_ui()

        txs: List[TxData] = []
        for wallet in wallet_manager().wallets:
            txs += wallet.get_txs()
        tx_history_rows = []
        for tx in sorted(txs, reverse=True):
            tx_history_row = TxSummaryRow(
                tx_data=tx,
                tx_icon=(
                    "arrow-top-right" if tx.balance_change < 0 else "arrow-bottom-right"
                ),
                tx_color="#abb8c3" if tx.balance_change < 0 else "green",
                tx_time=str(tx.timestamp) if (tx.timestamp) else "Pending",
                balance_change=exchange_rate_manager.format_balance(
                    abs(tx.balance_change),
                    tx.wallet.currency,
                ),
            )
            tx_history_rows.append(tx_history_row)
        self.ids.tx_history_list.data = [
            {
                "viewclass": "TransactionListItem",
                "tx_data": tx_history_row.tx_data,
                "tx_icon": tx_history_row.tx_icon,
                "tx_color": tx_history_row.tx_color,
                "tx_time": tx_history_row.tx_time,
                "label": limit_length(tx_history_row.tx_data.label, MAX_TX_LABEL_LEN),
                "balance_change": tx_history_row.balance_change,
                "manager": self.manager,
            }
            for tx_history_row in tx_history_rows
        ]

    @mainthread
    def on_tx_summaries_updated(self, refreshing_wallets):
        # In the main view, we only update the UI when it's refreshing all wallets
        if refreshing_wallets != wallet_manager().wallets:
            return

        # Refresh completed
        self.ids.refresh_layout.refresh_done()
        self.update_ui()
