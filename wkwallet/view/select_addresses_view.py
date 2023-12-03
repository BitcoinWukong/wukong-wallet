from typing import List

from db.address_data import AddressData
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import MDList
from model.wallet_account import WalletAccount
from view.components.select_address_list_item import SelectAddressListItem

Builder.load_file("view/select_addresses_view.kv")


class SelectAddressesView(Screen):
    account: WalletAccount = ObjectProperty()
    selected_addresses_list: List[AddressData] = ObjectProperty()

    selected_addresses_list_view: MDList = ObjectProperty()
    available_addresses_list_view: MDList = ObjectProperty()

    def on_pre_enter(self, *args):
        self.selected_addresses_list_view.clear_widgets()
        for address_data in self.selected_addresses_list:
            select_address_list_item = SelectAddressListItem(address_data=address_data)
            select_address_list_item.on_selected = self.on_address_selected
            self.selected_addresses_list_view.add_widget(select_address_list_item)

        self.available_addresses_list_view.clear_widgets()
        for address_data in self.account.active_addresses:
            if address_data.total_balance == 0:
                continue
            if address_data not in self.selected_addresses_list:
                select_address_list_item = SelectAddressListItem(
                    address_data=address_data
                )
                select_address_list_item.on_selected = self.on_address_selected
                self.available_addresses_list_view.add_widget(select_address_list_item)
        return super().on_pre_enter(*args)

    def on_address_selected(self, selected_address_list_item: SelectAddressListItem):
        if selected_address_list_item.address_data in self.selected_addresses_list:
            self.selected_addresses_list_view.remove_widget(selected_address_list_item)
            self.available_addresses_list_view.add_widget(selected_address_list_item)
            self.selected_addresses_list.remove(selected_address_list_item.address_data)
        else:
            self.available_addresses_list_view.remove_widget(selected_address_list_item)
            self.selected_addresses_list_view.add_widget(selected_address_list_item)
            self.selected_addresses_list.append(selected_address_list_item.address_data)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = "send_bitcoin_view"
