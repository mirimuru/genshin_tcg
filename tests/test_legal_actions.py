from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def action_types(actions):
    return {action.action_type for action in actions}


def test_generates_basic_actions_for_active_character():
    game = make_game()
    actions = game.get_legal_actions(0)
    assert action_types(actions) == {
        ActionType.NORMAL_ATTACK,
        ActionType.ELEMENTAL_SKILL,
        ActionType.END_ROUND,
        ActionType.SWITCH_CHARACTER,
    }
    assert {action.target for action in actions if action.action_type is ActionType.SWITCH_CHARACTER} == {1, 2}


def test_elemental_burst_is_available_when_energy_is_full():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = character.max_energy
    assert ActionType.ELEMENTAL_BURST in action_types(game.get_legal_actions(0))


def test_forced_switch_only_allows_switch_actions():
    game = make_game()
    game.state.players[0].active_character.hp = 0
    actions = game.get_legal_actions(0)
    assert action_types(actions) == {ActionType.SWITCH_CHARACTER}
    assert {action.target for action in actions} == {1, 2}


def test_defeated_player_has_no_legal_actions():
    game = make_game()
    for character in game.state.players[0].characters:
        character.hp = 0
    assert game.get_legal_actions(0) == []


def test_wrong_player_and_finished_game_have_no_legal_actions():
    game = make_game()
    assert game.get_legal_actions(1) == []
    game.state.game_over = True
    assert game.get_legal_actions(0) == []


def test_cpu_selects_from_legal_actions():
    game = make_game()
    legal = game.get_legal_actions(0)
    from players.cpu import CpuPlayer
    action = CpuPlayer().choose_action(game, 0, legal_actions=legal)
    assert action in legal
