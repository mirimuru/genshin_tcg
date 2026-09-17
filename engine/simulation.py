from copy import deepcopy

from engine.actions import Action
from engine.game import Game
from engine.state import GameState


def copy_state(state: GameState) -> GameState:
    """ゲーム状態を独立したオブジェクトとして複製する。"""
    if not isinstance(state, GameState):
        raise TypeError("state must be GameState")
    return state.copy()


def copy_game(game: Game) -> Game:
    """Gameと、その内部状態を独立したゲームとして複製する。"""
    if not isinstance(game, Game):
        raise TypeError("game must be Game")
    return deepcopy(game)


def simulate_action(game: Game, action: Action) -> Game:
    """元のGameを変更せず、指定Actionを複製先で実行した結果を返す。"""
    if not isinstance(action, Action):
        raise TypeError("action must be Action")
    simulated = copy_game(game)
    simulated.execute_action(action)
    return simulated
