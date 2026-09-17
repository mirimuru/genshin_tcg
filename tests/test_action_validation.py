import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


def make_player(player_id):
    return PlayerState(
        player_id,
        [
            CharacterState("Character 1", Element.PYRO),
            CharacterState("Character 2", Element.HYDRO),
            CharacterState("Character 3", Element.CRYO),
        ],
    )


def make_game():
    game = Game(GameState([make_player(0), make_player(1)]))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_is_action_legal_rejects_unexpected_target():
    game = make_game()
    action = Action(0, ActionType.NORMAL_ATTACK, target=1)

    assert game.is_action_legal(action) is False


def test_execute_action_rejects_action_that_is_not_legal():
    game = make_game()
    action = Action(0, ActionType.NORMAL_ATTACK, target=1)

    with pytest.raises(ValueError, match="合法なActionではありません"):
        game.execute_action(action)
