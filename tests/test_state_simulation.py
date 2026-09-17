import pytest

from engine.actions import Action, ActionType
from engine.game import Game
from engine.state import GameState


def make_game():
    game = Game.create_default()
    game.state.phase = game.state.phase.ACTION
    game.state.current_player = 0
    game.state.players[0].has_rerolled = True
    return game


def test_game_state_copy_is_independent():
    game = make_game()
    copied = game.state.copy()

    copied.players[0].characters[0].hp = 3
    copied.players[0].dice.dice.clear()
    copied.round_number = 99

    assert game.state.players[0].characters[0].hp == game.state.players[0].characters[0].max_hp
    assert game.state.players[0].dice.dice
    assert game.state.round_number == 1
    assert copied is not game.state
    assert copied.players[0] is not game.state.players[0]
    assert copied.players[0].characters[0] is not game.state.players[0].characters[0]


def test_game_copy_preserves_state_but_is_independent():
    game = make_game()
    copied = game.copy()

    assert copied is not game
    assert copied.state is not game.state
    assert copied.state.round_number == game.state.round_number
    assert copied.state.current_player == game.state.current_player
    assert copied.state.players[0].characters[0].hp == game.state.players[0].characters[0].hp

    copied.state.players[0].characters[0].hp = 1
    assert game.state.players[0].characters[0].hp == game.state.players[0].characters[0].max_hp


def test_simulate_action_does_not_mutate_original():
    game = make_game()
    game.state.players[0].dice.add(game.state.players[0].dice.dice.pop() if game.state.players[0].dice.dice else None)
    original_hp = game.state.players[0].characters[0].hp
    action = Action(0, ActionType.END_ROUND)

    simulated = game.simulate_action(action)

    assert game.state.players[0].characters[0].hp == original_hp
    assert game.state.current_player == 0
    assert game.state.phase is game.state.phase.ACTION
    assert simulated is not game
    assert simulated.state is not game.state


def test_simulate_action_rejects_illegal_action_without_mutating_original():
    game = make_game()
    action = Action(1, ActionType.END_ROUND)

    with pytest.raises(ValueError):
        game.simulate_action(action)

    assert game.state.current_player == 0
    assert game.state.phase is game.state.phase.ACTION


def test_game_state_copy_keeps_registries_and_status_definitions_usable():
    game = make_game()
    copied = game.state.copy()

    original = game.state.players[0].active_character
    clone = copied.players[0].active_character
    assert clone.definition.character_id == original.definition.character_id
    assert clone.definition.name == original.definition.name
