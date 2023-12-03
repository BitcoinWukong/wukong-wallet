from db.address_data import AddressData
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import ILeftBody, OneLineIconListItem
from model.exchange_rate_manager import exchange_rate_manager
from model.fidelity_bond import address_index_to_locktime
from model.wallet_account import WalletAccount
from utils import limit_length
from view.detail_views.address_details_view import AddressDetailsView

# TODO: Update Builder.load_file to use relative paths.
Builder.load_file("view/components/address_list_item.kv")
# Builder.load_file("./address_list_item.kv")

MAX_ADDR_LABEL_LEN = 19


class AddressListItem(OneLineIconListItem):
    manager: ScreenManager = ObjectProperty()
    account: WalletAccount = ObjectProperty()
    address_data: AddressData = ObjectProperty()

    balance_label: MDLabel = ObjectProperty()
    status_label: MDLabel = ObjectProperty()
    address_label: MDLabel = ObjectProperty()

    def update_ui(self, currency):
        self.balance_label.text = exchange_rate_manager.format_balance(
            self.address_data.total_balance,
            currency,
        )
        self.status_label.text = self.address_data.status
        if self.status_label.text == "coin-join":
            self.status_label.text = f"{self.status_label.text} ({self.address_data.utxos[0].anon_set_count})"

        for utxo in self.address_data.utxos:
            if utxo.tx.height <= 0:
                self.status_label.text = "pending " + self.status_label.text

        if self.address_data.label:
            self.address_label.text = limit_length(
                self.address_data.label, MAX_ADDR_LABEL_LEN
            )
        else:
            if self.address_data.chain_index == 0:
                self.address_label.text = f"external {self.address_data.address_index}"
            elif self.address_data.chain_index == 1:
                self.address_label.text = f"internal {self.address_data.address_index}"
            if self.address_data.chain_index == 2:
                locktime = address_index_to_locktime(self.address_data.address_index)
                self.address_label.text = f"fb {locktime.strftime('%Y-%m-%d')}"

    def on_release(self):
        address_details_view = AddressDetailsView(
            name="address_details_view",
            account=self.account,
            address_data=self.address_data,
        )

        self.manager.add_widget(address_details_view)
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = address_details_view.name


class AddressListItemBox(ILeftBody, MDBoxLayout):
    pass


# TODO: Move WidgetTestApp to a separate file and make it reusable.
from kivymd.app import MDApp


class WidgetTestApp(MDApp):
    def __init__(self, target_widget_class, **kwargs):
        self.target_widget_class = target_widget_class
        super().__init__(**kwargs)

    def build(self):
        return self.target_widget_class()


if __name__ == "__main__":
    from kivy.core.window import Window

    Window.top = 100
    Window.left = 2800
    WidgetTestApp(target_widget_class=AddressListItem).run()
