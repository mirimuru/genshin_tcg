from collections import Counter

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.simulation import expected_value, simulate_reroll


def test_simulate_reroll_replaces_only_selected_dice_with_probability(monkeypatch):
    class FakeDicePool:
        @classmethod
        def roll_outcomes(cls, count=DicePool.DEFAULT_DICE, dice_types=None):
            assert count == 2
            return [
                (DicePool({DiceType.PYRO: 2}), 0.25),
                (DicePool({DiceType.OMNI: 2}), 0.75),
            ]

    monkeypatch.setattr("engine.simulation.DicePool", FakeDicePool)
    game = _make_game()
    game.state.players[0].dice = DicePool({
        DiceType.PYRO: 2,
        DiceType.HYDRO: 2,
        DiceType.OMNI: 1,
    })
    game.state.players[1].dice = DicePool({DiceType.GEO: 8})

    action = Action(
        0,
        ActionType.REROLL_DICE,
        target=(DiceType.PYRO, DiceType.PYRO),
    )
    outcomes = simulate_reroll(game, action)

    assert len(outcomes) == 2
    assert sum(outcome.probability for outcome in outcomes) == 1.0
    assert outcomes[0].state.state.players[0].dice == DicePool({
        DiceType.PYRO: 2,
        DiceType.HYDRO: 2,
        DiceType.OMNI: 1,
    })
    assert outcomes[1].state.state.players[0].dice == DicePool({
        DiceType.OMNI: 3,
        DiceType.HYDRO: 2,
    })
    assert game.state.players[0].dice.count(DiceType.PYRO) == 2


def test_simulate_reroll_preserves_opponent_and_marks_reroll(monkeypatch):
    game = _make_game()
    game.state.players[0].dice = DicePool({DiceType.PYRO: 1, DiceType.HYDRO: 1})
    game.state.players[1].dice = DicePool({DiceType.GEO: 8})
    opponent_snapshot = game.state.players[1].dice.as_list()

    action = Action(0, ActionType.REROLL_DICE, target=(DiceType.PYRO,))
    outcome = simulate_reroll(game, action)[0].state

    assert outcome.state.players[0].has_rerolled is True
    assert outcome.state.players[1].dice.as_list() == opponent_snapshot
    assert outcome.state.players[1].dice is not game.state.players[1].dice
    assert outcome.state.current_player == 1
    assert outcome.state.phase.value == "roll"


def test_simulate_reroll_finishes_roll_phase_when_opponent_already_rerolled():
    game = _make_game()
    game.state.players[0].has_rerolled = False
    game.state.players[1].has_rerolled = True

    action = Action(0, ActionType.REROLL_DICE, target=())
    outcome = simulate_reroll(game, action)[0].state

    assert outcome.state.players[0].has_rerolled is True
    assert outcome.state.phase.value == "action"
    assert outcome.state.current_player == 0


def test_simulate_reroll_rejects_invalid_action():
    game = _make_game()

    for action in (
        Action(1, ActionType.REROLL_DICE, target=()),
        Action(0, ActionType.NORMAL_ATTACK),
    ):
        try:
            simulate_reroll(game, action)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid reroll action must raise ValueError")


def test_simulate_reroll_empty_selection_has_single_deterministic_outcome():
    game = _make_game()
    outcome = simulate_reroll(
        game,
        Action(0, ActionType.REROLL_DICE, target=()),
    )[0]

    assert outcome.probability == 1.0
    assert outcome.state.state.players[0].dice == game.state.players[0].dice


def test_simulate_reroll_expected_value_is_usable():
    game = _make_game()
    game.state.players[0].dice = DicePool({DiceType.PYRO: 1, DiceType.HYDRO: 1})

    outcomes = simulate_reroll(
        game,
        Action(0, ActionType.REROLL_DICE, target=(DiceType.PYRO,)),
    )

    assert expected_value(
        outcomes,
        lambda result: float(result.state.players[0].dice.total),
    ) == 2.0


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
