from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.textfield import MDTextField
from wallet_manager import wallet_manager


class MnemonicTab(MDFloatLayout, MDTabsBase):
    manager: ScreenManager = ObjectProperty()
    mnemonic_text_field: MDTextField = ObjectProperty()
    account_number_button: MDRaisedButton = ObjectProperty()

    def reset(self):
        self.mnemonic_text_field.text = ""
        self.account_number_button.text = "1"

        menu_items = [
            {
                "text": "1",
                "height": dp(50),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.update_account_number(1),
            },
            {
                "text": "2",
                "height": dp(50),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.update_account_number(2),
            },
            {
                "text": "3",
                "height": dp(50),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.update_account_number(3),
            },
            {
                "text": "4",
                "height": dp(50),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.update_account_number(4),
            },
            {
                "text": "5",
                "height": dp(50),
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.update_account_number(5),
            },
        ]
        self.menu = MDDropdownMenu(
            caller=self.account_number_button,
            items=menu_items,
        )

    def press_account_number_button(self):
        self.menu.open()

    def update_account_number(self, account_number: int):
        self.account_number_button.text = str(account_number)
        Clock.schedule_once(lambda dt: self.menu.dismiss(), 0.15)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = "main_view"

    def press_add(self):
        mnemonic = self.mnemonic_text_field.text.strip()

        if not wallet_manager().create_wallet_from_mnemonic(
            mnemonic=mnemonic,
            n_accounts=int(self.account_number_button.text),
        ):
            # TODO: Give an error message about invalid mnemonic
            return

        self.back()

        # TODO: Only refresh the newly added wallet.
        Clock.schedule_once(lambda dt: self.manager.main_view.refresh(), 0.5)
