import random

import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from players.cpu import CpuPlayer


def make_game(rng=None, prepare_action=True):
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players), rng=rng)
    if prepare_action:
        game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
        game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    return game


def test_default_dice_pool_contains_eight_dice():
    game = make_game()
    dice = game.state.players[0].dice
    assert isinstance(dice, DicePool)
    assert dice.total == 8


def test_dice_pool_can_pay_and_consumes_cost():
    dice = DicePool({DiceType.PYRO: 2, DiceType.OMNI: 1})
    cost = {DiceType.PYRO: 2, DiceType.OMNI: 1}
    assert dice.can_pay(cost)
    dice.pay(cost)
    assert dice.total == 0


def test_omni_dice_can_cover_elemental_cost():
    dice = DicePool({DiceType.OMNI: 3})
    assert dice.can_pay({DiceType.PYRO: 3})
    dice.pay({DiceType.PYRO: 3})
    assert dice.total == 0


def test_dice_pool_rejects_insufficient_cost():
    dice = DicePool({DiceType.PYRO: 1})
    with pytest.raises(ValueError):
        dice.pay({DiceType.PYRO: 2})


def test_roll_generates_eight_dice_from_all_elemental_types_and_omni():
    dice = DicePool.roll(random.Random(0), count=8)

    assert dice.total == 8
    assert dice.count(DiceType.CRYO) == 3
    assert dice.count(DiceType.ELECTRO) == 2
    assert dice.count(DiceType.GEO) == 2
    assert dice.count(DiceType.OMNI) == 1


def test_roll_rejects_invalid_count():
    with pytest.raises(ValueError):
        DicePool.roll(random.Random(0), count=-1)


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


def test_cpu_ends_round_when_no_action_can_afford_dice():
    game = make_game()
    game.state.players[0].dice = DicePool()
    legal_actions = game.get_legal_actions(0)
    action = CpuPlayer().choose_action(game, 0, legal_actions)
    assert action == Action(0, ActionType.END_ROUND)


def test_round_end_rolls_new_elemental_dice():
    game = make_game(random.Random(0), prepare_action=False)
    game.rng = random.Random(0)
    game.state.players[0].dice = DicePool({DiceType.OMNI: 1})
    game.state.players[1].dice = DicePool({DiceType.OMNI: 1})

    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))

    player0_dice = game.state.players[0].dice
    player1_dice = game.state.players[1].dice
    assert game.state.round_number == 2
    assert player0_dice.total == 8
    assert player1_dice.total == 8
    assert player0_dice.count(DiceType.CRYO) == 3
    assert player0_dice.count(DiceType.ELECTRO) == 2
    assert player0_dice.count(DiceType.GEO) == 2
    assert player0_dice.count(DiceType.OMNI) == 1
    assert player1_dice.count(DiceType.HYDRO) == 3
    assert player1_dice.count(DiceType.ELECTRO) == 2
    assert player1_dice.count(DiceType.DENDRO) == 1
    assert player1_dice.count(DiceType.ANEMO) == 1
    assert player1_dice.count(DiceType.PYRO) == 1


def test_harmonize_converts_one_unwanted_element_to_active_element():
    dice = DicePool({DiceType.HYDRO: 1, DiceType.PYRO: 2})

    dice.harmonize(DiceType.HYDRO, DiceType.PYRO)

    assert dice.count(DiceType.HYDRO) == 0
    assert dice.count(DiceType.PYRO) == 3
    assert dice.total == 3


def test_harmonize_rejects_same_element_and_omni_source():
    dice = DicePool({DiceType.PYRO: 2, DiceType.OMNI: 1})

    with pytest.raises(ValueError):
        dice.harmonize(DiceType.PYRO, DiceType.PYRO)
    with pytest.raises(ValueError):
        dice.harmonize(DiceType.OMNI, DiceType.PYRO)


def test_harmonize_rejects_missing_source_die():
    dice = DicePool({DiceType.HYDRO: 1})

    with pytest.raises(ValueError):
        dice.harmonize(DiceType.PYRO, DiceType.HYDRO)


def test_harmonize_action_is_legal_when_it_can_enable_attack():
    game = make_game()
    game.state.players[0].dice = DicePool({DiceType.HYDRO: 1, DiceType.PYRO: 2})

    actions = game.get_legal_actions(0)

    assert Action(0, ActionType.ELEMENTAL_TUNING, target=DiceType.HYDRO) in actions


def test_execute_harmonize_converts_die_to_active_element():
    game = make_game()
    game.state.players[0].dice = DicePool({DiceType.HYDRO: 1, DiceType.PYRO: 2})

    game.execute_action(Action(0, ActionType.ELEMENTAL_TUNING, target=DiceType.HYDRO))

    dice = game.state.players[0].dice
    assert dice.count(DiceType.HYDRO) == 0
    assert dice.count(DiceType.PYRO) == 3
    assert dice.total == 3


def test_cpu_uses_harmonize_when_it_can_enable_elemental_attack():
    game = make_game()
    game.state.players[0].dice = DicePool({DiceType.HYDRO: 1, DiceType.PYRO: 2})
    legal_actions = game.get_legal_actions(0)

    action = CpuPlayer().choose_action(game, 0, legal_actions)

    assert action == Action(0, ActionType.ELEMENTAL_TUNING, target=DiceType.HYDRO)
