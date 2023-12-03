from db.address_data import AddressData
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import ILeftBody, OneLineIconListItem

Builder.load_file("view/components/select_address_list_item.kv")


class SelectAddressListItem(OneLineIconListItem):
    address_data: AddressData = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_selected = None

    def on_release(self):
        if self.on_selected:
            self.on_selected(self)


class SelectAddressListItemBox(ILeftBody, MDBoxLayout):
    pass
