import math

from engine.dice import DicePool, DiceType
from engine.simulation import expected_value, simulate_roll


def test_simulate_roll_returns_independent_game_states_with_probabilities(monkeypatch):
    class FakeDicePool:
        @classmethod
        def roll_outcomes(cls, count=DicePool.DEFAULT_DICE, dice_types=None):
            return [
                (DicePool({DiceType.PYRO: count}), 0.25),
                (DicePool({DiceType.OMNI: count}), 0.75),
            ]

    monkeypatch.setattr("engine.simulation.DicePool", FakeDicePool)
    game = _make_game()
    original_dice = game.state.players[0].dice
    outcomes = simulate_roll(game, 0)

    assert len(outcomes) == 2
    assert math.isclose(sum(outcome.probability for outcome in outcomes), 1.0)
    assert outcomes[0].state is not game
    assert outcomes[0].state.state.players[0].dice.count(DiceType.PYRO) == DicePool.DEFAULT_DICE
    assert outcomes[1].state.state.players[0].dice.count(DiceType.OMNI) == DicePool.DEFAULT_DICE
    assert game.state.players[0].dice is original_dice


def test_simulate_roll_only_changes_requested_player(monkeypatch):
    class FakeDicePool:
        @classmethod
        def roll_outcomes(cls, count=DicePool.DEFAULT_DICE, dice_types=None):
            return [(DicePool({DiceType.GEO: count}), 1.0)]

    monkeypatch.setattr("engine.simulation.DicePool", FakeDicePool)
    game = _make_game()
    opponent_dice = game.state.players[1].dice
    opponent_snapshot = opponent_dice.as_list()
    outcome = simulate_roll(game, 0)[0].state

    assert outcome.state.players[0].dice.count(DiceType.GEO) == DicePool.DEFAULT_DICE
    assert outcome.state.players[1].dice.as_list() == opponent_snapshot
    assert outcome.state.players[1].dice is not opponent_dice


def test_simulate_roll_rejects_invalid_player():
    game = _make_game()
    for player_id in (-1, 2):
        try:
            simulate_roll(game, player_id)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid player_id must raise ValueError")


def test_roll_outcomes_are_usable_as_expected_value_inputs():
    outcomes = simulate_roll(_make_game(), 0, count=1)
    assert math.isclose(
        expected_value(outcomes, lambda game: float(game.state.players[0].dice.total)),
        1.0,
    )


def _make_game():
    from engine.game import Game
    from engine.state import CharacterState, Element, GameState, PlayerState

    def make_player(player_id):
        return PlayerState(
            player_id,
            [
                CharacterState("Character 1", Element.PYRO),
                CharacterState("Character 2", Element.HYDRO),
                CharacterState("Character 3", Element.CRYO),
            ],
        )

    return Game(GameState([make_player(0), make_player(1)]))
