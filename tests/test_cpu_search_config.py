from types import SimpleNamespace

import pytest

from engine.actions import Action, ActionType
from players.cpu import CpuPlayer


class FakeGame:
    def __init__(self, state, legal_actions=()):
        self.state = state
        self._legal_actions = list(legal_actions)

    def get_legal_actions(self, _player_id):
        return self._legal_actions


def test_cpu_search_depth_can_be_configured():
    cpu = CpuPlayer(search_depth=3)
    assert cpu.search_depth == 3


def test_cpu_rejects_non_positive_search_depth():
    with pytest.raises(ValueError):
        CpuPlayer(search_depth=0)
    with pytest.raises(ValueError):
        CpuPlayer(search_depth=-1)


def test_cpu_node_limit_stops_deep_search(monkeypatch):
    state = SimpleNamespace(game_over=False)
    action = Action(1, ActionType.NORMAL_ATTACK)
    game = FakeGame(state, [action])
    calls = []

    def fake_simulate_action(game, action):
        calls.append(action)
        return game

    def fake_evaluate_state(_state, _player_id):
        return 0.0

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    cpu = CpuPlayer(search_depth=4, max_search_nodes=2)
    result = cpu._search_value(game, 0, 1, 4)

    assert result == 0.0
    assert len(calls) <= 2
    assert cpu.last_search_nodes == 2
