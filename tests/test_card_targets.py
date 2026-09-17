from engine.actions import Action, ActionType
from engine.cards import CardDefinition, CardRegistry, CardTargetType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


class TargetCard(CardDefinition):
    card_id = "target_card"
    name = "対象テストカード"
    cost = {DiceType.ANY: 1}
    target_type = CardTargetType.ANY_ALLY_CHARACTER

    def play(self, game, player_id, target=None):
        game.state.players[player_id].active_character_index = target


class NoTargetCard(CardDefinition):
    card_id = "no_target_card"
    name = "対象なしテストカード"
    cost = {DiceType.ANY: 1}
    target_type = CardTargetType.NONE

    def play(self, game, player_id, target=None):
        pass


def make_game(card_registry):
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players), card_registry=card_registry)
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_any_ally_target_generates_one_action_per_alive_character():
    registry = CardRegistry([TargetCard])
    game = make_game(registry)
    game.state.players[0].hand = ["target_card"]

    actions = [action for action in game.get_legal_actions(0) if action.card_id == "target_card"]

    assert {action.target for action in actions} == {0, 1, 2}


def test_dead_ally_is_not_a_legal_card_target():
    registry = CardRegistry([TargetCard])
    game = make_game(registry)
    game.state.players[0].hand = ["target_card"]
    game.state.players[0].characters[1].hp = 0

    actions = [action for action in game.get_legal_actions(0) if action.card_id == "target_card"]

    assert {action.target for action in actions} == {0, 2}
    assert game.is_action_legal(Action(0, ActionType.PLAY_CARD, target=1, card_id="target_card")) is False


def test_none_target_card_only_accepts_none():
    registry = CardRegistry([NoTargetCard])
    game = make_game(registry)
    game.state.players[0].hand = ["no_target_card"]

    actions = [action for action in game.get_legal_actions(0) if action.card_id == "no_target_card"]

    assert actions == [Action(0, ActionType.PLAY_CARD, target=None, card_id="no_target_card")]
    assert game.is_action_legal(Action(0, ActionType.PLAY_CARD, target=0, card_id="no_target_card")) is False


def test_target_rule_is_checked_before_card_can_play():
    registry = CardRegistry([TargetCard])
    game = make_game(registry)
    game.state.players[0].hand = ["target_card"]
    game.state.players[0].characters[2].hp = 0

    assert registry.get("target_card").is_target_legal(game, 0, 0) is True
    assert registry.get("target_card").is_target_legal(game, 0, 2) is False


def test_execute_action_rejects_invalid_card_target():
    registry = CardRegistry([TargetCard])
    game = make_game(registry)
    game.state.players[0].hand = ["target_card"]
    game.state.players[0].characters[1].hp = 0

    action = Action(0, ActionType.PLAY_CARD, target=1, card_id="target_card")
    assert game.is_action_legal(action) is False
