from types import SimpleNamespace

from engine.actions import Action, ActionType
from players.cpu import CpuPlayer


def test_minimax_alpha_beta_prunes_unnecessary_sibling(monkeypatch):
    maximizing_state = SimpleNamespace(game_over=False)
    minimizing_state = SimpleNamespace(game_over=False)
    leaf_a = SimpleNamespace(game_over=False, name="a")
    leaf_b = SimpleNamespace(game_over=False, name="b")
    first = Action(1, ActionType.NORMAL_ATTACK)
    second = Action(1, ActionType.ELEMENTAL_SKILL)
    visited = []

    def fake_simulate_action(game, action):
        visited.append(action)
        if game is minimizing_state and action is first:
            return leaf_a
        if game is minimizing_state and action is second:
            return leaf_b
        return minimizing_state

    def fake_evaluate_state(state, _player_id):
        return {"a": 1.0, "b": 10.0}[state.name]

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    result = CpuPlayer._minimax(
        minimizing_state,
        root_player_id=0,
        current_player_id=1,
        depth=1,
        alpha=5.0,
        beta=float("inf"),
    )

    assert result == 1.0
    assert visited == [first]
