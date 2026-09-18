from types import SimpleNamespace

from engine.actions import Action, ActionType
from players.cpu import CpuPlayer


class FakeGame:
    def __init__(self, state, legal_actions=()):
        self.state = state
        self._legal_actions = list(legal_actions)

    def get_legal_actions(self, _player_id):
        return self._legal_actions


def test_search_cache_reuses_identical_state(monkeypatch):
    state = SimpleNamespace(game_over=False, phase=SimpleNamespace(value="action"))
    action = Action(1, ActionType.NORMAL_ATTACK)
    game = FakeGame(state, [action])
    calls = []

    def fake_simulate_action(current_game, _action):
        calls.append(current_game)
        return current_game

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", lambda _state, _player_id: 42.0)

    cpu = CpuPlayer(search_depth=2)
    first = cpu._search_value(game, 0, 1, 1)
    first_calls = len(calls)
    second = cpu._search_value(game, 0, 1, 1)

    assert first == second == 42.0
    assert first_calls == 1
    assert len(calls) == first_calls
    assert cpu.last_search_cache_hits >= 1


def test_search_cache_key_changes_when_state_changes():
    state_a = SimpleNamespace(game_over=False, phase=SimpleNamespace(value="action"), hp=10)
    state_b = SimpleNamespace(game_over=False, phase=SimpleNamespace(value="action"), hp=9)
    game_a = FakeGame(state_a)
    game_b = FakeGame(state_b)
    cpu = CpuPlayer(search_depth=2)

    assert cpu._search_cache_key(game_a, 0, 1, 2) != cpu._search_cache_key(game_b, 0, 1, 2)


def test_search_cache_is_cleared_for_each_root_search():
    state = SimpleNamespace(game_over=False, phase=SimpleNamespace(value="action"))
    game = FakeGame(state)
    cpu = CpuPlayer(search_depth=2)

    cpu._search_cache[("stale",)] = 99.0
    cpu._search_value(game, 0, 1, 0)

    assert ("stale",) not in cpu._search_cache
