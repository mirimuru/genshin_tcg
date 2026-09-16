import pytest

from engine.actions import Action, ActionType
from engine.cards import CardDefinition, CardRegistry
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


class HealCard(CardDefinition):
    card_id = "test_heal"
    name = "テスト回復"
    cost = {DiceType.ANY: 1}

    def play(self, game, player_id, target=None):
        character = game.state.players[player_id].active_character
        character.heal(2)


def make_game():
    players = [
        PlayerState(0, [
            CharacterState("A", Element.PYRO),
            CharacterState("B", Element.HYDRO),
            CharacterState("C", Element.CRYO),
        ]),
        PlayerState(1, [
            CharacterState("X", Element.PYRO),
            CharacterState("Y", Element.HYDRO),
            CharacterState("Z", Element.CRYO),
        ]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 3})
    players[1].dice = DicePool({DiceType.OMNI: 3})
    return game


def test_card_registry_resolves_card_by_id():
    registry = CardRegistry([HealCard])

    card = registry.get("test_heal")

    assert isinstance(card, HealCard)
    assert card.name == "テスト回復"


def test_play_card_pays_cost_removes_card_and_applies_effect():
    registry = CardRegistry([HealCard])
    game = make_game()
    game.card_registry = registry
    player = game.state.players[0]
    player.hand = ["test_heal"]
    player.active_character.hp = 5

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_heal"))

    assert player.active_character.hp == 7
    assert player.hand == []
    assert player.dice.total == 2
    assert game.state.current_player == 1


def test_play_card_requires_card_in_hand_and_sufficient_dice():
    registry = CardRegistry([HealCard])
    game = make_game()
    game.card_registry = registry

    with pytest.raises(ValueError, match="手札"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_heal"))

    player = game.state.players[0]
    player.hand = ["test_heal"]
    player.dice = DicePool({DiceType.OMNI: 0})

    with pytest.raises(ValueError, match="ダイス"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_heal"))

    assert player.hand == ["test_heal"]


def test_card_appears_in_legal_actions_when_playable():
    registry = CardRegistry([HealCard])
    game = make_game()
    game.card_registry = registry
    game.state.players[0].hand = ["test_heal"]

    actions = game.get_legal_actions(0)

    assert Action(0, ActionType.PLAY_CARD, card_id="test_heal") in actions
