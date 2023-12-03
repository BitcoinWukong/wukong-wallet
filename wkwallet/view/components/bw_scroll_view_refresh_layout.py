from kivymd.uix.refreshlayout import MDScrollViewRefreshLayout


class BWScrollViewRefreshLayout(MDScrollViewRefreshLayout):
    def on_touch_up(self, *args):
        if self._did_overscroll and not self._work_spinner:
            if self.refresh_callback:
                self.refresh_callback()
            self._work_spinner = True
            self._did_overscroll = False
            return True
        return super().on_touch_up(*args)

    def refresh_done(self) -> None:
        self._work_spinner = False
