import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from content.cards import JUEYUN_GUOBA, JueyunGuoba
from engine.cards import CardRegistry


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 3})
    players[1].dice = DicePool({DiceType.OMNI: 3})
    return game


def test_jueyun_guoba_has_stable_definition():
    assert isinstance(JUEYUN_GUOBA, JueyunGuoba)
    assert JUEYUN_GUOBA.card_id == "jueyun_guoba"
    assert JUEYUN_GUOBA.name == "絶雲の唐辛子"
    assert JUEYUN_GUOBA.cost == {DiceType.ANY: 1}


def test_jueyun_guoba_adds_combat_status_and_boosts_next_normal_attack():
    game = make_game()
    game.card_registry = CardRegistry([JUEYUN_GUOBA])
    player = game.state.players[0]
    target = game.state.players[1].active_character
    player.hand = ["jueyun_guoba"]

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="jueyun_guoba"))

    assert player.get_combat_status("jueyun_guoba") is not None
    assert player.get_combat_status("jueyun_guoba").usages == 1

    game.state.current_player = 0
    game.normal_attack(0)

    assert target.hp == 7
    assert player.get_combat_status("jueyun_guoba") is None


def test_jueyun_guoba_does_not_boost_elemental_skill():
    game = make_game()
    game.card_registry = CardRegistry([JUEYUN_GUOBA])
    player = game.state.players[0]
    target = game.state.players[1].active_character
    player.hand = ["jueyun_guoba"]

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="jueyun_guoba"))

    game.state.current_player = 0
    game.elemental_skill(0)

    assert target.hp == 7
    assert player.get_combat_status("jueyun_guoba") is not None
