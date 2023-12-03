from db.address_data import AddressData
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.textfield import MDTextField
from model.exchange_rate_manager import exchange_rate_manager, toggle_currency
from model.wallet_account import WalletAccount
from view.send_bitcoin_view import SendBitcoinView

Builder.load_file("view/detail_views/address_details_view.kv")


class AddressDetailsView(Screen):
    account: WalletAccount = ObjectProperty()
    address_data: AddressData = ObjectProperty()
    address_label_input: MDTextField = ObjectProperty()
    address_balance_label = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = "wallet_view"
        self.manager.remove_widget(self)

    def on_pre_leave(self, *args):
        self.address_data.label = self.address_label_input.text
        self.address_data.save()
        return super().on_pre_leave(*args)

    def on_pre_enter(self, *args):
        self.currency = "sat"
        self.update_balance()
        if self.address_data.private_key is None:
            self.ids.send_button.disabled = True
        else:
            self.ids.send_button.disabled = False
        return super().on_pre_enter(*args)

    def press_address_balance(self):
        self.currency = toggle_currency(self.currency, allow_hidden=False)
        self.update_balance()

    def update_balance(self):
        self.address_balance_label.text = exchange_rate_manager.format_balance(
            self.address_data.total_balance,
            self.currency,
        )

    def press_send(self) -> None:
        send_bitcoin_view: SendBitcoinView = self.manager.send_bitcoin_view
        send_bitcoin_view.account = self.account
        send_bitcoin_view.input_addresses_list = [self.address_data]
        send_bitcoin_view.back_view_name = self.name

        self.manager.transition.duration = 0.2
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = send_bitcoin_view.name
