from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty
from kivy.utils import platform

from hw import HW, HWFactory

__version__ = "0.2"


class CrazyBotGame(Widget):

    orient1 = NumericProperty(0)
    orient2 = NumericProperty(0)
    m1 = StringProperty("")
    m2 = StringProperty("")
    reverse = NumericProperty(0)
    device = StringProperty("nothing")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hw: HW | None = None

    def get_motor_data(self, z: int, y: int, r: int):
        """
        Differential drive mixer using two user sliders.
        Inputs:
          z: power from get_compass (0..100)
          y: turn from get_compass (-50..50)
          r: reverse flag, passed through
        Controls:
          powersl: 1..100 overall power scale
          turnsl: 1..100 turning aggressiveness
        Output:
          (left, right, r) where motors are 0..255
        """
        tpower = max(1, int(self.ids.powersl.value))
        tturn = max(1, int(self.ids.turnsl.value))
        power_scaled = max(0.0, min(float(z), 100.0)) / 100.0
        # More aggressive power response: slider gamma < 1
        power_gamma = 0.7
        effective_power_scale = (tpower / 100.0) ** power_gamma
        base_power = int(round(power_scaled * effective_power_scale * 255.0))
        turn_input = max(-50.0, min(float(y), 50.0)) / 50.0
        # More aggressive turn: lower exponent and slight input emphasis
        turn_gamma = 2.0
        a = (tturn / 100.0) ** turn_gamma
        input_gamma = 1.1
        scaled = (abs(turn_input) ** input_gamma) * a
        scaled = max(0.0, min(scaled, 1.0))
        left = base_power
        right = base_power
        if turn_input < 0:
            right = int(round(base_power * (1.0 - scaled)))
        elif turn_input > 0:
            left = int(round(base_power * (1.0 - scaled)))
        self.m1 = "%d %d" % (int(left), self.orient1)
        self.m2 = "%d %d" % (int(right), self.orient2)
        self.device = "%d / %d" % (tpower, tturn)
        # Use reverse flag to invert direction instead of modifying motor values
        r = 0 if r else 1
        return int(left), int(right), r

    def send_data(self, data):
        if self.hw:
            payload = "42,%d,119,%s," % (
                len(data) + 1,
                ",".join([str(a) for a in data]),
            )
            self.hw.send_data(payload, 200)

    def update(self, dt):
        if self.hw:
            (self.orient1, self.orient2) = self.hw.get_compass()
            v1, v2, r = self.get_motor_data(self.orient2, self.orient1, self.reverse)
            self.send_data([v1, v2, r])

    def init_hw(self):
        self.hw = HWFactory.get(platform)

    def check_hw(self, dt):
        if self.hw:
            self.hw.check()

    def _stop(self):
        if self.hw:
            self.hw.stop()

    def _start(self):
        if self.hw:
            self.hw.start()


class CrazyBotApp(App):
    def build(self):
        self._game: CrazyBotGame = CrazyBotGame()
        self._game.init_hw()
        Clock.schedule_interval(self._game.update, 1.0 / 60.0)
        Clock.schedule_interval(self._game.check_hw, 5.0)
        return self._game

    def on_stop(self):
        self._game._stop()

    def on_start(self):
        self._game._start()


if __name__ == "__main__":
    CrazyBotApp().run()
