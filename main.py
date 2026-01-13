from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty
from kivy.utils import platform
import math
from typing import override

__version__ = "0.1"


class HW:
    def __init__(self) -> None:
        self.load()

    def check(self) -> None:
        if self.device is None or self.hardware is None:
            self.load()

    def load(self):
        self.device = None
        self.hardware = None
        self.hw = None

    def get_compass(self) -> tuple[int, int]:
        o_turn, o_power = 0, 0
        return o_turn, o_power

    def send_data(self, data, timeout):
        if self.device:
            self.device.write(data.encode())

    def stop(self):
        pass

    def start(self):
        pass


class HWAndroid(HW):

    @override
    def load(self) -> None:
        HW.load(self)

        try:
            from usb4a import usb
            from usbserial4a import serial4a
            from plyer import spatialorientation

            spatialorientation.enable_listener()
            self.hardware = spatialorientation

            usb_device_list = usb.get_usb_device_list()
            device_name_list = [device.getDeviceName() for device in usb_device_list]
            print("DEVICS", device_name_list)
            device_name = device_name_list[0]
            device = usb.get_usb_device(device_name)
            if not usb.has_usb_permission(device):
                print("ASKING FOR USB PERMISSION")
                usb.request_usb_permission(device)
                return
            self.device = serial4a.get_serial_port(
                device_name, 57600, 8, "N", 1, timeout=1
            )
        except Exception as e:
            print("Disable hardware support")
            print(e)

    @override
    def start(self):
        if self.hardware:
            self.hardware.enable_listener()

    @override
    def stop(self):
        if platform == "android" and self.hardware:
            self.hardware.disable_listener()

    @override
    def get_compass(self) -> tuple[int, int]:
        """
        On Android, read phone orientation and scale values for control:
        - pitch (values[2]) in [-pi/2, 0] -> power 0..100
        - roll  (values[1]) in [-pi/2, +pi/2] -> turn -50..50
        Returns (turn, power) as integers.
        """
        o_turn, o_power = 0, 0
        if self.hardware:
            values = self.hardware.orientation
            if values[1] is not None and values[2] is not None:
                v_pitch = float(values[2])
                v_roll = float(values[1])
                v_pitch = max(-math.pi / 2, min(v_pitch, 0.0))
                v_roll = max(-math.pi / 2, min(v_roll, math.pi / 2))
                o_power = int((v_pitch + math.pi / 2) * (200.0 / math.pi))
                o_turn = int((v_roll + math.pi / 2) * (100.0 / math.pi)) - 50
        return o_turn, o_power


class HWLinux(HW):
    @override
    def load(self) -> None:
        import serial

        HW.load(self)

        try:
            self.device = serial.Serial("/dev/ttyUSB0", 57600, timeout=1)
            self.hardware = True
        except serial.SerialException as e:
            print("Disable hardware support")
            print(e)


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
        if platform == "android":
            self.hw = HWAndroid()
        elif platform == "linux":
            self.hw = HWLinux()

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
