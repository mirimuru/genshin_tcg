import pytest

from engine.actions import Action, ActionType
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from engine.dice import DiceType, DicePool


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    return Game(GameState(players))


def test_default_dice_pool_contains_eight_omni_dice():
    game = make_game()
    dice = game.state.players[0].dice
    assert isinstance(dice, DicePool)
    assert dice.total == 8
    assert dice.count(DiceType.OMNI) == 8


def test_dice_pool_can_pay_and_consumes_cost():
    dice = DicePool({DiceType.PYRO: 2, DiceType.OMNI: 1})
    cost = {DiceType.PYRO: 2, DiceType.OMNI: 1}
    assert dice.can_pay(cost)
    dice.pay(cost)
    assert dice.total == 0


def test_dice_pool_rejects_insufficient_cost():
    dice = DicePool({DiceType.PYRO: 1})
    with pytest.raises(ValueError):
        dice.pay({DiceType.PYRO: 2})


def test_attack_actions_require_three_dice():
    game = make_game()
    player = game.state.players[0]
    player.dice = DicePool()
    actions = game.get_legal_actions(0)
    assert Action(0, ActionType.NORMAL_ATTACK) not in actions
    assert Action(0, ActionType.ELEMENTAL_SKILL) not in actions
    assert Action(0, ActionType.END_ROUND) in actions


def test_switch_requires_one_die():
    game = make_game()
    player = game.state.players[0]
    player.dice = DicePool()
    assert Action(0, ActionType.SWITCH_CHARACTER, target=1) not in game.get_legal_actions(0)
    player.dice = DicePool({DiceType.OMNI: 1})
    assert Action(0, ActionType.SWITCH_CHARACTER, target=1) in game.get_legal_actions(0)


def test_executing_attack_consumes_three_dice():
    game = make_game()
    player = game.state.players[0]
    player.dice = DicePool({DiceType.OMNI: 3})
    player.active_character.definition = type("Definition", (), {"normal_attack": lambda self, game, player_id: None})()
    game.execute_action(Action(0, ActionType.NORMAL_ATTACK))
    assert player.dice.total == 0


def test_round_end_refills_simplified_dice_pool():
    game = make_game()
    game.state.players[0].dice = DicePool({DiceType.OMNI: 1})
    game.state.players[1].dice = DicePool({DiceType.OMNI: 1})
    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))
    assert game.state.round_number == 2
    assert game.state.players[0].dice.total == 8
    assert game.state.players[1].dice.total == 8
