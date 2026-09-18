from types import SimpleNamespace

from engine.actions import Action, ActionType
from players.cpu import CpuPlayer


class FakeGame:
    def __init__(self, state, legal_actions=()):
        self.state = state
        self._legal_actions = list(legal_actions)

    def get_legal_actions(self, _player_id):
        return self._legal_actions


def test_minimax_alpha_beta_prunes_unnecessary_sibling(monkeypatch):
    minimizing_state = SimpleNamespace(game_over=False)
    leaf_a = SimpleNamespace(game_over=False, name="a")
    leaf_b = SimpleNamespace(game_over=False, name="b")
    first = Action(1, ActionType.NORMAL_ATTACK)
    second = Action(1, ActionType.ELEMENTAL_SKILL)
    root_game = FakeGame(minimizing_state, [first, second])
    visited = []

    def fake_simulate_action(game, action):
        visited.append(action)
        if game is root_game and action is first:
            return FakeGame(leaf_a)
        if game is root_game and action is second:
            return FakeGame(leaf_b)
        raise AssertionError("枝刈りされた兄弟Actionはシミュレーションされない")

    def fake_evaluate_state(state, _player_id):
        return {"a": 1.0, "b": 10.0}[state.name]

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    result = CpuPlayer._minimax(
        root_game,
        root_player_id=0,
        current_player_id=1,
        depth=1,
        alpha=5.0,
        beta=float("inf"),
    )

    assert result == 1.0
    assert visited == [first]
