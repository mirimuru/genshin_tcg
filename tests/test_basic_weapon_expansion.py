from engine.actions import Action, ActionType
from engine.characters import CharacterDefinition as PublicCharacterDefinition
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from content.cards.weapons import (
    MagicGuide,
    RavenBow,
    WhiteIronGreatsword,
    WhiteTassel,
)


class ClaymoreCharacter(PublicCharacterDefinition):
    character_id = "test_basic_claymore"
    name = "テスト両手剣"
    element = Element.PYRO
    weapon_type = "claymore"


class PolearmCharacter(PublicCharacterDefinition):
    character_id = "test_basic_polearm"
    name = "テスト長柄武器"
    element = Element.HYDRO
    weapon_type = "polearm"


class BowCharacter(PublicCharacterDefinition):
    character_id = "test_basic_bow"
    name = "テスト弓"
    element = Element.CRYO
    weapon_type = "bow"


class CatalystCharacter(PublicCharacterDefinition):
    character_id = "test_basic_catalyst"
    name = "テスト法器"
    element = Element.ELECTRO
    weapon_type = "catalyst"


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


def test_basic_weapon_cards_match_all_weapon_types_and_cost_active_element():
    cases = [
        (WhiteIronGreatsword(), ClaymoreCharacter(), DiceType.PYRO),
        (WhiteTassel(), PolearmCharacter(), DiceType.HYDRO),
        (RavenBow(), BowCharacter(), DiceType.CRYO),
        (MagicGuide(), CatalystCharacter(), DiceType.ELECTRO),
    ]

    for card, character, dice_type in cases:
        game = make_game(character)
        game.state.players[0].dice = DicePool({dice_type: 2})
        game.card_registry.register(card)
        action = Action(0, ActionType.PLAY_CARD, card_id=card.card_id)

        assert card.can_play(game, 0)
        assert game.get_action_cost(action) == {dice_type: 2}


def test_basic_weapon_cards_reject_wrong_weapon_type():
    for card in (WhiteIronGreatsword(), WhiteTassel(), RavenBow(), MagicGuide()):
        game = make_game(ClaymoreCharacter())
        game.state.players[0].dice = DicePool({DiceType.PYRO: 2})
        assert card.can_play(game, 0) is (card is WhiteIronGreatsword())


def test_basic_weapon_adds_one_damage_only_to_normal_attack():
    cases = [
        (WhiteIronGreatsword(), ClaymoreCharacter()),
        (WhiteTassel(), PolearmCharacter()),
        (RavenBow(), BowCharacter()),
        (MagicGuide(), CatalystCharacter()),
    ]

    for card, character in cases:
        game = make_game(character)
        game.state.players[0].active_character.add_equipment(card.create_status())
        opponent = game.state.players[1].active_character

        game.normal_attack(0)
        assert opponent.hp == 7

        game.elemental_skill(0)
        assert opponent.hp == 4
