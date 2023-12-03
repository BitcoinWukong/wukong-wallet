from abc import abstractmethod

from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy_garden.zbarcam import ZBarCam

Builder.load_file("view/scan_qr_code_view.kv")
from kivy.logger import Logger


class QRScanObserver:
    @abstractmethod
    def on_scan(self, scan_str):
        pass


class ScanQRCodeView(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.zbarcam = None
        self.observer = None  # type: QRScanObserver
        self.back_view_name = "main_view"

    def on_pre_enter(self, *args):
        if self.zbarcam is None:
            self.zbarcam = ZBarCam()
            self.zbarcam.bind(symbols=self.on_symbols_update)
            self.ids.box_layout.add_widget(self.zbarcam)
        else:
            self.zbarcam.start()
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        self.zbarcam.stop()
        return super().on_pre_leave(*args)

    @mainthread
    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = self.back_view_name

    def on_symbols_update(self, _, symbols):
        Logger.debug(f"WKWallet: on_symbols_update, {symbols}")

        if len(symbols) > 0:
            if self.observer:
                self.observer.on_scan(symbols[0].data.decode("UTF-8"))
            self.back()
