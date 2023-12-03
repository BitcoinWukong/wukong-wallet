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
from model.wallet_account import WalletAccount
from view.components.address_list_item import AddressListItem
from wallet import Wallet

Builder.load_file("view/wallet_view/wallet_addresses_tab.kv")

UNUSED_ADDRESSES_GAP_LIMIT = 5


class AccountAddressesList(MDList):
    pass


class WalletAddressesTab(MDFloatLayout, MDTabsBase):
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
            first_unused_index = (
                self.wallet.accounts[account_index].data.chains[0].first_unused_index
            )

            panel_text = f"Account {account_index}"
            panel_secondary_text = f"first new external address: {first_unused_index}"
            if panel_index >= 0:
                account_panel = self.root_list_view.children[panel_index]
                account_panel.panel_cls.text = panel_text
                account_panel.panel_cls.secondary_text = panel_secondary_text
                panel_index -= 1
            else:
                account_panel = MDExpansionPanel(
                    content=AccountAddressesList(),
                    panel_cls=MDExpansionPanelTwoLine(
                        text=panel_text,
                        secondary_text=panel_secondary_text,
                    ),
                )
                self.root_list_view.add_widget(account_panel)

            if self.update_account_addresses_ui(
                addresses_md_list=account_panel.content,
                account=self.wallet.accounts[account_index],
            ):
                # Close the panel if it's open
                if account_panel.get_state() == "open":
                    account_panel.check_open_panel(account_panel.panel_cls)

        # Remove extra account panels
        while len(self.root_list_view.children) > len(self.wallet.accounts):
            self.root_list_view.remove_widget(self.root_list_view.children[0])

    def update_single_account_ui(self) -> None:
        self.update_account_addresses_ui(
            addresses_md_list=self.root_list_view,
            account=self.wallet.accounts[0],
        )

    def update_account_addresses_ui(
        self,
        addresses_md_list: MDList,
        account: WalletAccount,
    ) -> bool:
        """
        Update the target MDList with the unused addresses of the given account.
        """
        if any(type(item) != AddressListItem for item in addresses_md_list.children):
            addresses_md_list.clear_widgets()

        first_unused_index = account.data.chains[0].first_unused_index

        unused_addresses = []
        for i in range(5):
            address_data = self.wallet.addr_indexes_to_data.get(
                (account.data.account_index, 0, first_unused_index + i)
            )
            if address_data is not None:
                unused_addresses.append(address_data)

        needs_refresh = len(addresses_md_list.children) < UNUSED_ADDRESSES_GAP_LIMIT
        if not needs_refresh:
            for address_list_item in addresses_md_list.children:
                if address_list_item.address_data not in unused_addresses:
                    needs_refresh = True
                    break

        if needs_refresh:
            addresses_md_list.clear_widgets()
            for address_data in unused_addresses:
                if not address_data.status:
                    address_data.status = "new"
                    address_data.save()
                address_list_item = AddressListItem(
                    account=account,
                    address_data=address_data,
                    manager=self.manager,
                )
                addresses_md_list.add_widget(address_list_item)

        # Update all address list items
        for address_list_item in addresses_md_list.children:
            address_list_item.update_ui(self.wallet.data.currency)

        return needs_refresh
