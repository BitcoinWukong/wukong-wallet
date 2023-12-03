from db.tx_data import TxData
from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import ILeftBody, OneLineIconListItem
from view.detail_views.transaction_details_view import TransactionDetailsView

Builder.load_file("view/components/transaction_list_item.kv")

MAX_TX_LABEL_LEN = 24


class TransactionListItem(OneLineIconListItem):
    tx_data: TxData = ObjectProperty()
    tx_icon = StringProperty()
    tx_color = ColorProperty()
    tx_time = StringProperty()
    balance_change = StringProperty()
    label = StringProperty()
    manager: ScreenManager = ObjectProperty()

    def on_release(self):
        tx_details_view = TransactionDetailsView(
            name="tx_details_view",
            tx_data=self.tx_data,
            back_view_name=self.manager.current,
        )

        self.manager.add_widget(tx_details_view)
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = tx_details_view.name


class TransactionListItemBox(ILeftBody, MDBoxLayout):
    pass
