import random

import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from players.cpu import CpuPlayer


def make_game(rng=None):
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    return Game(GameState(players), rng=rng)


def test_game_starts_in_roll_phase_with_eight_dice_for_both_players():
    game = make_game(random.Random(0))

    assert game.state.phase is GamePhase.ROLL
    assert game.state.players[0].dice.total == 8
    assert game.state.players[1].dice.total == 8
    assert not game.state.players[0].has_rerolled
    assert not game.state.players[1].has_rerolled


def test_reroll_replaces_only_selected_dice_and_preserves_total():
    dice = DicePool({DiceType.PYRO: 2, DiceType.HYDRO: 2, DiceType.OMNI: 4})

    dice.reroll({DiceType.PYRO: 2}, random.Random(0))

    assert dice.total == 8
    assert dice.count(DiceType.PYRO) == 0


def test_reroll_rejects_more_selected_dice_than_available():
    dice = DicePool({DiceType.PYRO: 1})

    with pytest.raises(ValueError):
        dice.reroll({DiceType.PYRO: 2}, random.Random(0))


def test_roll_phase_exposes_reroll_actions():
    game = make_game(random.Random(0))

    actions = game.get_legal_actions(0)

    assert Action(0, ActionType.REROLL_DICE, target=()) in actions
    assert any(
        action.action_type is ActionType.REROLL_DICE and action.target
        for action in actions
    )


def test_first_player_rerolls_then_second_player_rerolls_and_action_phase_starts():
    game = make_game(random.Random(0))
    first = Action(0, ActionType.REROLL_DICE, target=(DiceType.CRYO,))
    second = Action(1, ActionType.REROLL_DICE, target=())

    game.execute_action(first)

    assert game.state.phase is GamePhase.ROLL
    assert game.state.current_player == 1
    assert game.state.players[0].has_rerolled

    game.execute_action(second)

    assert game.state.phase is GamePhase.ACTION
    assert game.state.current_player == 0
    assert game.state.players[1].has_rerolled


def test_player_cannot_reroll_twice():
    game = make_game(random.Random(0))
    action = Action(0, ActionType.REROLL_DICE, target=())

    game.execute_action(action)

    with pytest.raises(ValueError):
        game.execute_action(action)


def test_cpu_rerolls_non_matching_dice_for_active_element():
    game = make_game(random.Random(0))
    player = game.state.players[0]
    player.dice = DicePool({DiceType.PYRO: 2, DiceType.HYDRO: 2, DiceType.CRYO: 2, DiceType.OMNI: 2})

    action = CpuPlayer().choose_action(game, 0, game.get_legal_actions(0))

    assert action.action_type is ActionType.REROLL_DICE
    assert action.target == (DiceType.HYDRO, DiceType.HYDRO, DiceType.CRYO, DiceType.CRYO)


def test_round_end_enters_roll_phase_and_resets_reroll_flags():
    game = make_game(random.Random(0))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    assert game.state.phase is GamePhase.ACTION

    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))

    assert game.state.round_number == 2
    assert game.state.phase is GamePhase.ROLL
    assert game.state.current_player == 0
    assert not game.state.players[0].has_rerolled
    assert not game.state.players[1].has_rerolled
    assert game.state.players[0].dice.total == 8
    assert game.state.players[1].dice.total == 8
