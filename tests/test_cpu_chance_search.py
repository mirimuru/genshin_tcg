from types import SimpleNamespace

from engine.actions import Action, ActionType
from engine.simulation import ChanceOutcome
from players.cpu import CpuPlayer


def test_cpu_evaluates_dice_roll_as_expected_value(monkeypatch):
    game = SimpleNamespace(state=SimpleNamespace(game_over=False))
    cpu = CpuPlayer(search_depth=2)
    first_state = SimpleNamespace(value=2.0)
    second_state = SimpleNamespace(value=8.0)

    monkeypatch.setattr(
        "players.cpu.simulate_roll",
        lambda _game, _player_id: [
            ChanceOutcome(first_state, 0.25),
            ChanceOutcome(second_state, 0.75),
        ],
    )
    monkeypatch.setattr(
        "players.cpu.evaluate_state",
        lambda state, _player_id: state.value,
    )

    assert cpu._evaluate_chance_roll(game, 0) == 6.5


def test_cpu_chance_roll_search_recurses_into_each_outcome(monkeypatch):
    game = SimpleNamespace(state=SimpleNamespace(game_over=False))
    cpu = CpuPlayer(search_depth=2)
    first_state = SimpleNamespace(value=3.0)
    second_state = SimpleNamespace(value=9.0)
    searched = []

    monkeypatch.setattr(
        "players.cpu.simulate_roll",
        lambda _game, _player_id: [
            ChanceOutcome(first_state, 0.5),
            ChanceOutcome(second_state, 0.5),
        ],
    )

    def fake_search_node(state, root_player_id, current_player_id, depth, alpha, beta):
        searched.append((state, root_player_id, current_player_id, depth))
        return state.value

    monkeypatch.setattr(cpu, "_search_node", fake_search_node)

    assert cpu._evaluate_chance_roll(game, 0, depth=2) == 6.0
    assert searched == [
        (first_state, 0, 0, 1),
        (second_state, 0, 0, 1),
    ]


def test_cpu_chance_roll_returns_static_evaluation_at_zero_depth(monkeypatch):
    game = SimpleNamespace(state=SimpleNamespace(game_over=False))
    cpu = CpuPlayer(search_depth=2)

    monkeypatch.setattr("players.cpu.evaluate_state", lambda _state, _player_id: 4.0)

    assert cpu._evaluate_chance_roll(game, 0, depth=0) == 4.0
