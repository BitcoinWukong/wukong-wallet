from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.selectioncontrol.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField
from settings_manager import settings_manager
from wallet import Wallet
from wallet_manager import wallet_manager

Builder.load_file("view/edit_wallet_view.kv")


class EditWalletView(Screen):
    wallet_name_input = ObjectProperty()  # type: MDTextField
    xpub_input = ObjectProperty()  # type: MDTextField
    fidelity_bond_switch = ObjectProperty()  # type: MDSwitch

    def __init__(self, **kw):
        super().__init__(**kw)

    def on_pre_enter(self, *args):
        self.wallet_name_input.text = self.wallet.data.name
        self.xpub_input.text = self.wallet.xpub
        self.fidelity_bond_switch.active = self.wallet.data.has_fidelity_bonds
        return super().on_pre_enter(*args)

    def back(self, target_view_name="wallet_view"):
        self.manager.transition.direction = "down"
        self.manager.transition.mode = "pop"
        self.manager.current = target_view_name

    def on_pre_leave(self, *args):
        self.wallet.set_wallet_name(self.wallet_name_input.text)
        active_value = self.fidelity_bond_switch.active
        if active_value != self.wallet.data.has_fidelity_bonds:
            self.wallet.enable_disable_fidelity_bonds(active_value)
            wallet_manager().refresh(target_wallets=[self.wallet])
        return super().on_pre_leave(*args)

    def set_wallet(self, wallet: Wallet):
        self.wallet = wallet

    def press_delete(self):
        wallet_manager().remove_wallet(self.wallet.data)
        self.back(target_view_name="main_view")
        self.manager.main_view.refresh()
