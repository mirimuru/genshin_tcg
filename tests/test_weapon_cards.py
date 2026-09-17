from engine.actions import Action, ActionType
from engine.cards import CardDefinition, CardRegistry
from engine.characters import CharacterDefinition as PublicCharacterDefinition
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterDefinition, CharacterState, Element, GamePhase, GameState, PlayerState
from engine.statuses import EquipmentStatusDefinition, StatusInstance
from content.cards.weapons import TravelerHandySword, TRAVELER_HANDY_SWORD, TravelerHandySwordStatus


class SwordCharacter(PublicCharacterDefinition):
    character_id = "test_sword_character"
    name = "テスト片手剣キャラクター"
    element = Element.PYRO
    weapon_type = "sword"


class ClaymoreCharacter(PublicCharacterDefinition):
    character_id = "test_claymore_character"
    name = "テスト両手剣キャラクター"
    element = Element.PYRO
    weapon_type = "claymore"


class TestWeaponStatus(EquipmentStatusDefinition):
    status_id = "test_weapon_status"
    name = "テスト武器"
    equipment_slot = "weapon"
    weapon_type = "sword"


class TestOtherWeaponStatus(EquipmentStatusDefinition):
    status_id = "test_other_weapon_status"
    name = "テスト別武器"
    equipment_slot = "weapon"
    weapon_type = "sword"


class TestCard(CardDefinition):
    card_id = "test_card"
    name = "テストカード"
    cost = {DiceType.ANY: 1}

    def play(self, game, player_id, target=None):
        pass


def make_game(character_definition=None):
    character_definition = character_definition or SwordCharacter()
    players = [
        PlayerState(0, [character_definition.create_state(), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.HYDRO), CharacterState("Y", Element.PYRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 8})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_character_definition_has_optional_weapon_type():
    character = SwordCharacter()
    assert character.weapon_type == "sword"
    assert CharacterDefinition("legacy", "旧キャラ", Element.PYRO).weapon_type is None


def test_weapon_status_uses_weapon_equipment_slot():
    status = StatusInstance(TestWeaponStatus)

    assert isinstance(status.definition, EquipmentStatusDefinition)
    assert status.definition.equipment_slot == "weapon"
    assert status.definition.weapon_type == "sword"


def test_character_replaces_existing_weapon_equipment_only():
    character = SwordCharacter().create_state()
    first = StatusInstance(TestWeaponStatus)
    second = StatusInstance(TestOtherWeaponStatus)
    talent = StatusInstance(type("TestTalentStatus", (EquipmentStatusDefinition,), {
        "status_id": "test_talent_status",
        "name": "テスト天賦",
        "equipment_slot": "talent",
    }))

    character.add_equipment(first)
    character.add_equipment(talent)
    character.add_equipment(second)

    assert character.get_status("test_weapon_status") is None
    assert character.get_status("test_other_weapon_status") is second
    assert character.get_status("test_talent_status") is talent


def test_weapon_card_requires_matching_weapon_type():
    game = make_game(SwordCharacter())
    card = TravelerHandySword()
    game.state.players[0].dice = DicePool({DiceType.PYRO: 2})

    assert card.can_play(game, 0)

    game = make_game(ClaymoreCharacter())
    game.state.players[0].dice = DicePool({DiceType.PYRO: 2})
    assert not card.can_play(game, 0)


def test_weapon_card_requires_matching_elemental_dice():
    game = make_game(SwordCharacter())
    card = TravelerHandySword()
    game.state.players[0].dice = DicePool({DiceType.HYDRO: 2})

    assert not card.can_play(game, 0)


def test_weapon_card_uses_active_character_element_for_cost():
    game = make_game(SwordCharacter())
    card = TravelerHandySword()
    game.card_registry = CardRegistry([card])
    game.state.players[0].dice = DicePool({DiceType.PYRO: 2})

    assert game.get_action_cost(Action(0, ActionType.PLAY_CARD, card_id="traveler_handy_sword")) == {DiceType.PYRO: 2}


def test_weapon_card_equips_status():
    game = make_game(SwordCharacter())
    game.card_registry = CardRegistry([TRAVELER_HANDY_SWORD])
    player = game.state.players[0]
    player.hand = ["traveler_handy_sword"]
    player.dice = DicePool({DiceType.PYRO: 2})

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="traveler_handy_sword"))

    equipped = player.active_character.get_status("traveler_handy_sword")
    assert equipped is not None
    assert isinstance(equipped.definition, TravelerHandySwordStatus)
    assert player.dice.total == 0
    assert player.hand == []


def test_traveler_handy_sword_adds_one_damage_to_normal_attack():
    game = make_game(SwordCharacter())
    player = game.state.players[0]
    player.active_character.add_equipment(StatusInstance(TravelerHandySwordStatus))
    opponent = game.state.players[1].active_character

    game.normal_attack(0)

    assert opponent.hp == 7


def test_traveler_handy_sword_does_not_modify_elemental_skill():
    game = make_game(SwordCharacter())
    player = game.state.players[0]
    player.active_character.add_equipment(StatusInstance(TravelerHandySwordStatus))
    opponent = game.state.players[1].active_character

    game.elemental_skill(0)

    assert opponent.hp == 7
