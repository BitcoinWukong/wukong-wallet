from typing import List

from db.address_data import AddressData
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.expansionpanel.expansionpanel import (
    MDExpansionPanel,
    MDExpansionPanelTwoLine,
)
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import MDList
from kivymd.uix.tab import MDTabsBase
from model.exchange_rate_manager import exchange_rate_manager
from model.wallet_account import WalletAccount
from view.components.address_list_item import AddressListItem
from wallet import Wallet

Builder.load_file("view/wallet_view/wallet_coins_tab.kv")


class AccountCoinsList(MDList):
    pass


class WalletCoinsTab(MDFloatLayout, MDTabsBase):
    manager: ScreenManager = ObjectProperty()
    wallet: Wallet = ObjectProperty()

    root_list_view: MDList = ObjectProperty()

    @mainthread
    def update_ui(self) -> None:
        if len(self.wallet.accounts) > 1:
            self.update_multi_account_ui()
        else:
            self.update_single_account_ui()

    def update_multi_account_ui(self) -> None:
        if any(type(item) != MDExpansionPanel for item in self.root_list_view.children):
            self.root_list_view.clear_widgets()

        panel_index = len(self.root_list_view.children) - 1
        for account_index in self.wallet.accounts:
            account = self.wallet.accounts[account_index]

            panel_text = f"Account {account_index}"
            panel_secondary_text = exchange_rate_manager.format_balance(
                account.balance, self.wallet.data.currency
            )
            if panel_index >= 0:
                account_panel = self.root_list_view.children[panel_index]
                account_panel.panel_cls.text = panel_text
                account_panel.panel_cls.secondary_text = panel_secondary_text
                panel_index -= 1
            else:
                account_panel = MDExpansionPanel(
                    content=AccountCoinsList(),
                    panel_cls=MDExpansionPanelTwoLine(
                        text=panel_text,
                        secondary_text=panel_secondary_text,
                    ),
                )
                self.root_list_view.add_widget(account_panel)

            if self.update_account_coins_ui(
                coins_md_list=account_panel.content,
                account=account,
            ):
                # Close the panel if it's open
                if account_panel.get_state() == "open":
                    account_panel.check_open_panel(account_panel.panel_cls)

        # Remove extra account panels
        while len(self.root_list_view.children) > len(self.wallet.accounts):
            self.root_list_view.remove_widget(self.root_list_view.children[0])

    def update_single_account_ui(self) -> None:
        self.update_account_coins_ui(
            coins_md_list=self.root_list_view,
            account=self.wallet.accounts[0],
        )

    def update_account_coins_ui(
        self,
        coins_md_list: MDList,
        account: WalletAccount,
    ) -> bool:
        """
        Update the target MDList with the active addresses of the given account.
        """
        if any(type(item) != AddressListItem for item in coins_md_list.children):
            coins_md_list.clear_widgets()

        account_addresses: List[AddressData] = sorted(
            list(account.active_addresses),
            key=lambda addr: [addr.chain_index, addr.address_index],
        )

        needs_refresh = len(coins_md_list.children) < len(account_addresses)
        if not needs_refresh:
            for address_list_item in coins_md_list.children:
                if address_list_item.address_data not in account_addresses:
                    needs_refresh = True
                    break

        if needs_refresh:
            coins_md_list.clear_widgets()
            for address_data in account_addresses:
                if address_data.total_balance > 0:
                    address_list_item = AddressListItem(
                        account=account,
                        address_data=address_data,
                        manager=self.manager,
                    )
                    coins_md_list.add_widget(address_list_item)

        # Update all address list items
        for address_list_item in coins_md_list.children:
            address_list_item.update_ui(self.wallet.data.currency)

        return needs_refresh
