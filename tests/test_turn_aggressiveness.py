import math
import importlib
import pytest

from tests.test_main import load_game_with_platform


def test_full_turn_only_near_max_slider(monkeypatch):
    mod, game = load_game_with_platform(monkeypatch, "linux")
    game.ids.powersl.value = 100
    game.ids.turnsl.value = 80
    left, right, r = game.get_motor_data(100, 50, 0)
    assert right == 255 and left < 255
    assert r == 1
    game.ids.turnsl.value = 100
    left2, right2, r2 = game.get_motor_data(100, 50, 0)
    assert right2 == 255 and left2 == 0
    assert r2 == 1
