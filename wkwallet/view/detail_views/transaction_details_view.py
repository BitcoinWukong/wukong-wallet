from db.tx_data import TxData
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.textfield import MDTextField

Builder.load_file("view/detail_views/transaction_details_view.kv")


class TransactionDetailsView(Screen):
    tx_data: TxData = ObjectProperty()
    tx_label_input: MDTextField = ObjectProperty()

    def __init__(self, back_view_name="main_view", **kw):
        self.back_view_name = back_view_name
        super().__init__(**kw)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = self.back_view_name
        self.manager.remove_widget(self)

    def on_pre_enter(self, *args):
        self.ids.balance_change_label.text = "{:,}".format(self.tx_data.balance_change)
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        self.tx_data.label = self.tx_label_input.text
        self.tx_data.save()
        return super().on_pre_leave(*args)
