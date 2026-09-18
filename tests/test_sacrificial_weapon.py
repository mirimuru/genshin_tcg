from engine.actions import Action, ActionType
from engine.characters import CharacterDefinition as PublicCharacterDefinition
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from content.cards.weapons import SacrificialSword


class SwordCharacter(PublicCharacterDefinition):
    character_id = "test_sacrificial_sword"
    name = "テスト片手剣"
    element = Element.PYRO
    weapon_type = "sword"

    normal_attack_cost = {DiceType.PYRO: 3}
    elemental_skill_cost = {DiceType.PYRO: 3}


def make_game():
    players = [
        PlayerState(0, [SwordCharacter.create_state(), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.GEO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.PYRO: 8})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_sacrificial_sword_has_matching_weapon_type_and_cost():
    card = SacrificialSword()
    game = make_game()
    game.card_registry.register(card)
    game.state.players[0].dice = DicePool({DiceType.PYRO: 2})

    assert card.can_play(game, 0)
    assert game.get_action_cost(Action(0, ActionType.PLAY_CARD, card_id=card.card_id)) == {DiceType.PYRO: 2}


def test_sacrificial_sword_reduces_next_skill_cost_after_skill():
    card = SacrificialSword()
    game = make_game()
    game.state.players[0].active_character.add_equipment(card.create_status())

    skill = Action(0, ActionType.ELEMENTAL_SKILL)
    attack = Action(0, ActionType.NORMAL_ATTACK)

    assert game.get_action_cost(skill) == {DiceType.PYRO: 3}
    game.elemental_skill(0)

    assert game.get_action_cost(attack) == {DiceType.PYRO: 2}
    assert game.get_action_cost(attack) == {DiceType.PYRO: 2}

    game.normal_attack(0)
    assert game.get_action_cost(attack) == {DiceType.PYRO: 3}


def test_sacrificial_sword_does_not_apply_before_skill_or_to_other_character():
    card = SacrificialSword()
    game = make_game()
    game.state.players[0].active_character.add_equipment(card.create_status())

    attack = Action(0, ActionType.NORMAL_ATTACK)
    assert game.get_action_cost(attack) == {DiceType.PYRO: 3}

    game.state.players[0].active_character_index = 1
    assert game.get_action_cost(attack) == {DiceType.HYDRO: 3}
