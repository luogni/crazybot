from typing import override
from hw import HW
from serial import Serial, SerialException


class HWLinux(HW):

    def __init__(self):
        super().__init__()
        self._device: Serial | None = None
        self._o_turn: int = 0
        self._o_power: int = 0

    @override
    def send_data(self, data: str, timeout: int):
        if self._device:
            _ = self._device.write(data.encode())

    @override
    def check_and_load(self) -> None:
        super().check_and_load()

        try:
            self._device = Serial("/dev/ttyUSB0", 57600, timeout=1)
        except SerialException as e:
            print("Disable hardware support")
            print(e)

    @override
    def get_compass(self) -> tuple[int, int]:
        return self._o_turn, self._o_power

    @override
    def stop(self):
        if self._device:
            self._device.close()

    @override
    def start(self):
        pass

    @override
    def handle_key(self, key: int):
        # up = 273
        # down = 274
        # right = 275
        # left = 276
        if key == 273:
            self._o_power += 4
        elif key == 274:
            self._o_power -= 4
        elif key == 275:
            self._o_turn += 4
        elif key == 276:
            self._o_turn -= 4

        self._o_power = min(100, max(0, self._o_power))
        self._o_turn = min(50, max(-50, self._o_turn))
