from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from engine.actions import Action
from engine.game import Game
from engine.state import GameState


StateT = TypeVar("StateT")


@dataclass(frozen=True)
class ChanceOutcome(Generic[StateT]):
    """確率的な結果と、その結果が発生する確率。"""

    state: StateT
    probability: float

    def __post_init__(self):
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")


def expected_value(
    outcomes: list[ChanceOutcome[StateT]],
    value_function: Callable[[StateT], float],
) -> float:
    """確率結果から期待値を計算する。"""
    probability_sum = sum(outcome.probability for outcome in outcomes)
    if outcomes and abs(probability_sum - 1.0) > 1e-9:
        raise ValueError("outcome probabilities must sum to 1")
    return sum(
        outcome.probability * value_function(outcome.state)
        for outcome in outcomes
    )


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
