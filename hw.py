import math
from typing import override
from abc import abstractmethod, ABC


class HW(ABC):
    def __init__(self) -> None:
        self.check_and_load()

    @abstractmethod
    def check_and_load(self):
        pass

    @abstractmethod
    def get_compass(self) -> tuple[int, int]:
        o_turn, o_power = 0, 0
        return o_turn, o_power

    @abstractmethod
    def send_data(self, data, timeout):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass


class HWFactory:
    @staticmethod
    def get(platform: str) -> HW:
        if platform == "android":
            return HWAndroid()
        elif platform == "linux":
            return HWLinux()
        else:
            raise ValueError(f"platform not supported: {platform}")


class HWAndroid(HW):

    def __init__(self):
        super().__init__()
        self._device = None
        self._hardware = None

    @override
    def check_and_load(self) -> None:
        super().check_and_load()

        try:
            from usb4a import usb
            from usbserial4a import serial4a
            from plyer import spatialorientation

            spatialorientation.enable_listener()
            self._hardware = spatialorientation

            usb_device_list = usb.get_usb_device_list()
            device_name_list = [device.getDeviceName() for device in usb_device_list]
            print("DEVICS", device_name_list)
            device_name = device_name_list[0]
            device = usb.get_usb_device(device_name)
            if not usb.has_usb_permission(device):
                print("ASKING FOR USB PERMISSION")
                usb.request_usb_permission(device)
                return
            self._device = serial4a.get_serial_port(
                device_name, 57600, 8, "N", 1, timeout=1
            )
        except Exception as e:
            print("Disable hardware support")
            print(e)

    @override
    def send_data(self, data, timeout):
        if self._device:
            self._device.write(data.encode())

    @override
    def start(self):
        if self._hardware:
            self._hardware.enable_listener()

    @override
    def stop(self):
        if self._hardware:
            self._hardware.disable_listener()
        if self._device:
            self._device.close()

    @override
    def get_compass(self) -> tuple[int, int]:
        """
        On Android, read phone orientation and scale values for control:
        - pitch (values[2]) in [-pi/2, 0] -> power 0..100
        - roll  (values[1]) in [-pi/2, +pi/2] -> turn -50..50
        Returns (turn, power) as integers.
        """
        o_turn, o_power = 0, 0
        if self._hardware:
            values = self._hardware.orientation
            if values[1] is not None and values[2] is not None:
                v_pitch = float(values[2])
                v_roll = float(values[1])
                v_pitch = max(-math.pi / 2, min(v_pitch, 0.0))
                v_roll = max(-math.pi / 2, min(v_roll, math.pi / 2))
                o_power = int((v_pitch + math.pi / 2) * (200.0 / math.pi))
                o_turn = int((v_roll + math.pi / 2) * (100.0 / math.pi)) - 50
        return o_turn, o_power


class HWLinux(HW):

    def __init__(self):
        super().__init__()
        self._device = None

    @override
    def send_data(self, data: str, timeout: int):
        if self._device:
            _ = self._device.write(data.encode())

    @override
    def check_and_load(self) -> None:
        import serial

        super().check_and_load()

        try:
            self._device = serial.Serial("/dev/ttyUSB0", 57600, timeout=1)
        except serial.SerialException as e:
            print("Disable hardware support")
            print(e)

    @override
    def get_compass(self) -> tuple[int, int]:
        o_turn, o_power = 0, 0
        return o_turn, o_power

    @override
    def stop(self):
        if self._device:
            self._device.close()

    @override
    def start(self):
        pass
