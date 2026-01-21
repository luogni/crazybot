from abc import abstractmethod, ABC
from dataclasses import dataclass


@dataclass
class ControlWheel:
    """
    About where do I want to go and how fast

    Attributes:
       turn (int): -50 to 50
       power (int): 0 to 100
    """

    turn: int = 0
    power: int = 0


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

    def get_control_wheel(self) -> ControlWheel:
        (t, p) = self.get_compass()
        return ControlWheel(turn=t, power=p)

    @abstractmethod
    def send_data(self, data: str, timeout: int):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def handle_key(self, key: int):
        pass


class HWFactory:
    @staticmethod
    def get(platform: str) -> HW:
        """
        Factory to get correct HW class for current platform.
        """
        if platform == "android":
            from hwandroid import HWAndroid

            return HWAndroid()
        elif platform == "linux":
            from hwlinux import HWLinux

            return HWLinux()
        else:
            raise ValueError(f"platform not supported: {platform}")
