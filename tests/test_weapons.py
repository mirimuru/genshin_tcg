import pytest

from engine.cards import WeaponCardDefinition
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from engine.statuses import EquipmentStatusDefinition, StatusInstance, WeaponEquipmentStatusDefinition
from content.cards.weapons import TRAVELERS_HANDY_SWORD, TravelersHandySwordStatus


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 8})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_weapon_equipment_status_uses_weapon_slot_and_type():
    status = StatusInstance(TravelersHandySwordStatus)

    assert status.definition.equipment_slot == "weapon"
    assert status.definition.weapon_type == "sword"


def test_character_definition_exposes_weapon_type():
    from engine.characters import CharacterDefinition

    character = CharacterDefinition("test", "テスト", Element.PYRO, weapon_type="sword")

    assert character.weapon_type == "sword"
    assert character.create_state().definition.weapon_type == "sword"


def test_weapon_card_definition_requires_matching_weapon_type():
    game = make_game()
    game.state.players[0].active_character.definition.weapon_type = "sword"

    assert TRAVELERS_HANDY_SWORD.can_play(game, 0)

    game.state.players[0].active_character.definition.weapon_type = "bow"
    assert not TRAVELERS_HANDY_SWORD.can_play(game, 0)


def test_equipping_weapon_replaces_previous_weapon_but_keeps_talent():
    class SwordStatus(WeaponEquipmentStatusDefinition):
        status_id = "sword_a"
        name = "剣A"
        weapon_type = "sword"

    class SwordStatusB(WeaponEquipmentStatusDefinition):
        status_id = "sword_b"
        name = "剣B"
        weapon_type = "sword"

    class TalentStatus(EquipmentStatusDefinition):
        status_id = "talent"
        name = "天賦"
        equipment_slot = "talent"

    character = make_game().state.players[0].active_character
    character.add_equipment(StatusInstance(TalentStatus))
    character.add_equipment(StatusInstance(SwordStatus))
    character.add_equipment(StatusInstance(SwordStatusB))

    assert character.has_status("talent")
    assert not character.has_status("sword_a")
    assert character.has_status("sword_b")


def test_travelers_handy_sword_increases_only_normal_attack_damage():
    game = make_game()
    game.state.players[0].active_character.definition.weapon_type = "sword"
    game.state.players[0].active_character.add_equipment(StatusInstance(TravelersHandySwordStatus))

    game.normal_attack(0)
    assert game.state.players[1].active_character.hp == 7

    game.elemental_skill(0)
    assert game.state.players[1].active_character.hp == 4


def test_weapon_card_rejects_invalid_weapon_type():
    class InvalidWeaponCard(WeaponCardDefinition):
        card_id = "invalid_weapon"
        name = "不正武器"
        weapon_type = "boomerang"

        def create_status(self):
            return None

    with pytest.raises(ValueError, match="weapon_type"):
        InvalidWeaponCard()
