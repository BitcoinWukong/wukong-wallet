from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from .mnemonic_tab import MnemonicTab
from .watch_only_tab import WatchOnlyTab

Builder.load_file("view/add_wallet_view/add_wallet_view.kv")


class AddWalletView(Screen):
    mnemonic_tab: MnemonicTab = ObjectProperty()
    watch_only_tab: WatchOnlyTab = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.should_reset = True

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = "main_view"

    def on_pre_enter(self, *args):
        if self.should_reset:
            self.reset()
        else:
            self.should_reset = True
        return super().on_pre_enter(*args)

    def reset(self):
        self.mnemonic_tab.reset()
        self.watch_only_tab.reset()
