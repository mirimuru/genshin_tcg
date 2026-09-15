import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]
        players.append(PlayerState(player_id, characters))

    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_burning_reaction_applies_burning_status():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO

    game.deal_damage(0, 1, 2, Element.PYRO)

    assert "burning" in target.statuses
    assert target.hp == 7
    assert target.elemental_aura is None


def test_burning_status_deals_one_damage_at_end_of_round_and_is_removed():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 2, Element.PYRO)
    hp_before = target.hp

    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))

    assert hp_before - target.hp == 1
    assert "burning" not in target.statuses


def test_burning_damage_can_end_the_game():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.DENDRO
    target.receive_damage(7)
    target_player.characters[1].receive_damage(999)
    target_player.characters[2].receive_damage(999)

    game.deal_damage(0, 1, 1, Element.PYRO)
    assert "burning" in target.statuses
    assert target.hp == 1
    assert not game.state.game_over

    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))

    assert target.hp == 0
    assert game.state.game_over


def test_reapplying_burning_does_not_duplicate_status():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.PYRO)

    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.PYRO)

    assert target.statuses.count("burning") == 1
