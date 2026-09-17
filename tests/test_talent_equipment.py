import pytest

from content.cards import COLD_BLOODED_STRIKE
from content.characters import KAEYA
from engine.actions import Action, ActionType
from engine.cards import CardRegistry
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [KAEYA.create_state(), CharacterState("B", Element.HYDRO), CharacterState("C", Element.PYRO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.CRYO: 4})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_cold_blooded_strike_is_talent_equipment():
    assert COLD_BLOODED_STRIKE.card_id == "cold_blooded_strike"
    assert COLD_BLOODED_STRIKE.name == "冷血の剣"
    assert COLD_BLOODED_STRIKE.cost == {DiceType.CRYO: 4}
    assert COLD_BLOODED_STRIKE.equipment_slot == "talent"
    assert COLD_BLOODED_STRIKE.required_character_id == "kaeya"


def test_talent_card_equips_and_immediately_uses_skill():
    game = make_game()
    game.card_registry = CardRegistry([COLD_BLOODED_STRIKE])
    player = game.state.players[0]
    opponent = game.state.players[1].active_character
    player.hand = ["cold_blooded_strike"]
    player.active_character.hp = 8

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="cold_blooded_strike"))

    assert player.hand == []
    assert player.active_character.has_status("cold_blooded_strike")
    assert player.active_character.hp == 10
    assert opponent.hp == 7


def test_talent_heals_after_skill_only_once_per_round():
    game = make_game()
    game.card_registry = CardRegistry([COLD_BLOODED_STRIKE])
    player = game.state.players[0]
    player.hand = ["cold_blooded_strike"]
    player.active_character.hp = 8

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="cold_blooded_strike"))
    assert player.active_character.hp == 10

    player.active_character.hp = 7
    game.state.current_player = 0
    game.elemental_skill(0)
    assert player.active_character.hp == 7

    game.state.round_number += 1
    player.active_character.hp = 7
    game.state.current_player = 0
    game.elemental_skill(0)
    assert player.active_character.hp == 9


def test_talent_card_requires_kaeya_as_active_character():
    game = make_game()
    game.card_registry = CardRegistry([COLD_BLOODED_STRIKE])
    player = game.state.players[0]
    player.hand = ["cold_blooded_strike"]
    player.active_character_index = 1

    with pytest.raises(ValueError, match="そのカードを使用できません"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="cold_blooded_strike"))


def test_talent_equipment_replaces_existing_same_slot():
    game = make_game()
    character = game.state.players[0].active_character
    character.add_equipment(COLD_BLOODED_STRIKE.create_status())
    character.add_equipment(COLD_BLOODED_STRIKE.create_status())
    assert [status.status_id for status in character.statuses].count("cold_blooded_strike") == 1
