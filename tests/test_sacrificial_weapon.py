from engine.actions import Action, ActionType
from engine.characters import CharacterDefinition as PublicCharacterDefinition
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from content.cards.weapons import (
    SacrificialBow,
    SacrificialFragments,
    SacrificialGreatsword,
    SacrificialSword,
)


class SwordCharacter(PublicCharacterDefinition):
    character_id = "test_sacrificial_sword"
    name = "テスト片手剣"
    element = Element.PYRO
    weapon_type = "sword"
    normal_attack_cost = {DiceType.PYRO: 3}
    elemental_skill_cost = {DiceType.PYRO: 3}


class GreatswordCharacter(PublicCharacterDefinition):
    character_id = "test_sacrificial_greatsword"
    name = "テスト両手剣"
    element = Element.PYRO
    weapon_type = "claymore"
    normal_attack_cost = {DiceType.PYRO: 3}
    elemental_skill_cost = {DiceType.PYRO: 3}


class BowCharacter(PublicCharacterDefinition):
    character_id = "test_sacrificial_bow"
    name = "テスト弓"
    element = Element.CRYO
    weapon_type = "bow"
    normal_attack_cost = {DiceType.CRYO: 3}
    elemental_skill_cost = {DiceType.CRYO: 3}


class CatalystCharacter(PublicCharacterDefinition):
    character_id = "test_sacrificial_fragments"
    name = "テスト法器"
    element = Element.ELECTRO
    weapon_type = "catalyst"
    normal_attack_cost = {DiceType.ELECTRO: 3}
    elemental_skill_cost = {DiceType.ELECTRO: 3}


SWORD_CHARACTER = SwordCharacter()
GREATSWORD_CHARACTER = GreatswordCharacter()
BOW_CHARACTER = BowCharacter()
CATALYST_CHARACTER = CatalystCharacter()


def make_game(character_definition):
    players = [
        PlayerState(0, [character_definition.create_state(), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.GEO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 8})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_sacrificial_weapon_cards_match_weapon_type_and_cost():
    cases = [
        (SacrificialSword(), SWORD_CHARACTER, DiceType.PYRO),
        (SacrificialGreatsword(), GREATSWORD_CHARACTER, DiceType.PYRO),
        (SacrificialBow(), BOW_CHARACTER, DiceType.CRYO),
        (SacrificialFragments(), CATALYST_CHARACTER, DiceType.ELECTRO),
    ]
    for card, character, dice_type in cases:
        game = make_game(character)
        game.state.players[0].dice = DicePool({dice_type: 3})
        game.card_registry.register(card)
        action = Action(0, ActionType.PLAY_CARD, card_id=card.card_id)
        assert card.can_play(game, 0)
        assert game.get_action_cost(action) == {dice_type: 3}


def test_sacrificial_weapon_cards_reject_wrong_weapon_type():
    cases = [
        (SacrificialSword(), GreatswordCharacter()),
        (SacrificialGreatsword(), SwordCharacter()),
        (SacrificialBow(), CatalystCharacter()),
        (SacrificialFragments(), BowCharacter()),
    ]
    for card, wrong_character in cases:
        game = make_game(wrong_character)
        game.state.players[0].dice = DicePool({DiceType.PYRO: 3, DiceType.CRYO: 3, DiceType.ELECTRO: 3})
        assert card.can_play(game, 0) is False


def test_sacrificial_weapon_reduces_next_attack_action_cost_after_skill():
    cases = [
        (SacrificialSword(), SWORD_CHARACTER, DiceType.PYRO),
        (SacrificialGreatsword(), GREATSWORD_CHARACTER, DiceType.PYRO),
        (SacrificialBow(), BOW_CHARACTER, DiceType.CRYO),
        (SacrificialFragments(), CATALYST_CHARACTER, DiceType.ELECTRO),
    ]
    for card, character, dice_type in cases:
        game = make_game(character)
        game.state.players[0].active_character.add_equipment(card.create_status())
        skill = Action(0, ActionType.ELEMENTAL_SKILL)
        attack = Action(0, ActionType.NORMAL_ATTACK)
        assert game.get_action_cost(skill) == {dice_type: 3}
        game.elemental_skill(0)
        assert game.get_action_cost(attack) == {dice_type: 2}
        game.normal_attack(0)
        assert game.get_action_cost(attack) == {dice_type: 3}
