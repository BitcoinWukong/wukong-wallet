from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from utils import get_logs

Builder.load_file("view/app_log_view.kv")


class AppLogView(Screen):
    # files/app/.kivy/logs/kivy_23-06-12_3.txt
    logs_text_field = ObjectProperty()

    def on_pre_enter(self, *args):
        self.logs_text_field.text = get_logs()
        return super().on_pre_enter(*args)

    def back(self):
        self.manager.transition.direction = "down"
        self.manager.transition.mode = "pop"
        self.manager.current = self.manager.main_view.name
