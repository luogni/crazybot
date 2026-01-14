import math
import types
import builtins
import pytest

from kivy.utils import platform as kivy_platform

import importlib


class DummySpatial:
    def __init__(self, roll=None, pitch=None):
        self._roll = roll
        self._pitch = pitch
        self.enabled = False

    @property
    def orientation(self):
        return (None, self._roll, self._pitch)

    def enable_listener(self):
        self.enabled = True

    def disable_listener(self):
        self.enabled = False


class DummySlider:
    def __init__(self, value):
        self.value = value


class DummyIds(dict):
    def __getattr__(self, k):
        return self[k]


@pytest.fixture(autouse=True)
def reload_main(monkeypatch):
    monkeypatch.setenv("KIVY_WINDOW", "mock")
    yield


def load_game_with_platform(monkeypatch, platform_name="linux", spatial=None):
    monkeypatch.setenv("KIVY_WINDOW", "mock")
    # Patch kivy.utils.platform
    import kivy.utils as ku

    monkeypatch.setattr(ku, "platform", platform_name, raising=False)
    # Ensure our module sees patched platform
    mod = importlib.import_module("main")
    modhw = importlib.import_module("hw")
    importlib.reload(mod)
    game = mod.CrazyBotGame()
    # Inject HW with given spatial when android
    if platform_name == "android":
        hw = modhw.HWAndroid()
        hw.hardware = spatial
        game.hw = hw
    else:
        # Linux: avoid serial usage
        hw = modhw.HWLinux()
        hw.device = None
        game.hw = hw
    # Inject dummy sliders
    game.ids = DummyIds(powersl=DummySlider(70), turnsl=DummySlider(40))
    return mod, game


@pytest.mark.parametrize(
    "roll,pitch,exp_turn,exp_power",
    [
        (0.0, -math.pi / 2, 0, 0),  # centered, flat -> power=0, turn=0
        (math.pi / 2, -math.pi / 2, 50, 0),  # full right roll -> +50
        (-math.pi / 2, -math.pi / 2, -50, 0),  # full left roll -> -50
        (0.0, 0.0, 0, 100),  # fully pitched -> max power
        (0.0, -math.pi / 4, 0, 50),  # mid pitch -> ~50
    ],
)
def test_get_compass_scaling_android(monkeypatch, roll, pitch, exp_turn, exp_power):
    spatial = DummySpatial(roll=roll, pitch=pitch)
    mod, game = load_game_with_platform(monkeypatch, "android", spatial)
    t, p = game.hw.get_compass()
    assert -50 <= t <= 50
    assert 0 <= p <= 100
    assert t == exp_turn
    assert p == exp_power


@pytest.mark.parametrize(
    "z,y,power_scale,turn_scale,exp_left,exp_right",
    [
        (0, 0, 100, 100, 0, 0),
        (100, 0, 100, 100, 255, 255),
        (100, 50, 100, 100, 0, 255),
        (100, -50, 100, 100, 255, 0),
        (50, 0, 100, 100, 128, 128),
        (100, 25, 100, 50, 225, 255),
        (100, 25, 50, 100, 84, 157),
    ],
)
def test_get_motor_data(
    monkeypatch, z, y, power_scale, turn_scale, exp_left, exp_right
):
    mod, game = load_game_with_platform(monkeypatch, "linux")
    game.ids.powersl.value = power_scale
    game.ids.turnsl.value = turn_scale
    left, right, r = game.get_motor_data(z, y, 0)
    assert left == exp_left
    assert right == exp_right
    assert r == 1


def test_turn_clamping_and_scaling(monkeypatch):
    mod, game = load_game_with_platform(monkeypatch, "linux")
    game.ids.powersl.value = 100
    game.ids.turnsl.value = 25
    left, right, _ = game.get_motor_data(100, 50, 0)
    assert 0 <= left <= 255 and 0 <= right <= 255


def test_power_clamping(monkeypatch):
    mod, game = load_game_with_platform(monkeypatch, "linux")
    game.ids.powersl.value = 10
    left, right, _ = game.get_motor_data(150, 0, 0)
    assert 0 <= left <= 255 and 0 <= right <= 255
