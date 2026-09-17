import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.simulation import copy_game, simulate_action
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState(f"キャラクター{index}", Element.PYRO)
            for index in range(3)
        ]
        players.append(PlayerState(player_id, characters))
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    game.state.players[0].has_rerolled = True
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_game_state_copy_is_independent():
    game = make_game()
    copied = game.state.copy()

    copied.players[0].characters[0].hp = 3
    copied.players[0].dice.add(DiceType.PYRO, 2)
    copied.round_number = 99

    assert game.state.players[0].characters[0].hp == game.state.players[0].characters[0].max_hp
    assert game.state.players[0].dice.count(DiceType.PYRO) == 0
    assert copied.round_number == 99
    assert game.state.round_number == 1
    assert copied is not game.state
    assert copied.players[0] is not game.state.players[0]
    assert copied.players[0].characters[0] is not game.state.players[0].characters[0]


def test_game_copy_preserves_state_but_is_independent():
    game = make_game()
    copied = copy_game(game)

    assert copied is not game
    assert copied.state is not game.state
    assert copied.state.round_number == game.state.round_number
    assert copied.state.current_player == game.state.current_player
    assert copied.state.players[0].characters[0].hp == game.state.players[0].characters[0].hp

    copied.state.players[0].characters[0].hp = 1
    assert game.state.players[0].characters[0].hp == game.state.players[0].characters[0].max_hp


def test_simulate_action_does_not_mutate_original():
    game = make_game()
    original_hp = game.state.players[0].characters[0].hp
    action = Action(0, ActionType.END_ROUND)

    simulated = simulate_action(game, action)

    assert game.state.players[0].characters[0].hp == original_hp
    assert game.state.current_player == 0
    assert game.state.phase is GamePhase.ACTION
    assert simulated is not game
    assert simulated.state is not game.state


def test_simulate_action_rejects_illegal_action_without_mutating_original():
    game = make_game()
    action = Action(1, ActionType.END_ROUND)

    with pytest.raises(ValueError):
        simulate_action(game, action)

    assert game.state.current_player == 0
    assert game.state.phase is GamePhase.ACTION


def test_game_state_copy_keeps_character_definitions_usable():
    game = make_game()
    copied = game.state.copy()

    original = game.state.players[0].active_character
    clone = copied.players[0].active_character
    assert clone.definition.character_id == original.definition.character_id
    assert clone.definition.name == original.definition.name
