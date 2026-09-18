from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar
from collections import Counter

from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import GamePhase, GameState


StateT = TypeVar("StateT")
DEFAULT_ROLL_DICE = DicePool.DEFAULT_DICE


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


def simulate_roll(game: Game, player_id: int, count: int | None = None) -> list[ChanceOutcome[Game]]:
    """指定プレイヤーのダイスロールをChance Nodeとして展開する。

    元のGameは変更せず、各ダイス結果ごとに独立したGameを生成する。
    通常プレイの乱数ロールとは別に、CPU探索用の決定論的な展開を提供する。
    """
    if not isinstance(game, Game):
        raise TypeError("game must be Game")
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    if count is None:
        count = DEFAULT_ROLL_DICE
    if count < 0:
        raise ValueError("dice count must not be negative")

    outcomes = DicePool.roll_outcomes(count)
    return [
        ChanceOutcome(
            state=_game_with_dice(game, player_id, dice_pool),
            probability=probability,
        )
        for dice_pool, probability in outcomes
    ]


def simulate_reroll(game: Game, action: Action) -> list[ChanceOutcome[Game]]:
    """リロールActionを乱数なしのChance Nodeへ展開する。

    選択されていないダイスは保持し、選択された個数だけを全確率結果へ
    置き換える。元のGameは変更せず、各結果は独立したGameとなる。
    """
    if not isinstance(game, Game):
        raise TypeError("game must be Game")
    if not isinstance(action, Action):
        raise TypeError("action must be Action")
    if action.action_type is not ActionType.REROLL_DICE:
        raise ValueError("action must be REROLL_DICE")
    player_id = action.player_id
    if player_id not in (0, 1):
        raise ValueError("invalid player_id")
    if game.state.phase is not GamePhase.ROLL:
        raise ValueError("reroll simulation requires ROLL phase")
    if player_id != game.state.current_player:
        raise ValueError("action player is not current player")
    if game.state.players[player_id].has_rerolled:
        raise ValueError("player has already rerolled")
    if not isinstance(action.target, tuple):
        raise ValueError("reroll target must be a tuple")

    selected = Counter(action.target)
    player = game.state.players[player_id]
    original = player.dice.as_list()
    if any(dice_type not in DicePool.ROLLABLE_DICE_TYPES for dice_type in selected):
        raise ValueError("reroll target contains invalid dice")
    if any(player.dice.count(dice_type) < count for dice_type, count in selected.items()):
        raise ValueError("reroll target exceeds owned dice")

    selected_count = sum(selected.values())
    kept = Counter(original)
    kept.subtract(selected)
    if any(count < 0 for count in kept.values()):
        raise ValueError("reroll target exceeds owned dice")

    outcomes = DicePool.roll_outcomes(selected_count)
    result = []
    for rolled_pool, probability in outcomes:
        dice = DicePool(kept)
        for dice_type, count in rolled_pool._dice.items():
            dice.add(dice_type, count)
        simulated = copy_game(game)
        simulated.state.players[player_id].dice = dice
        simulated.state.players[player_id].has_rerolled = True

        opponent_id = 1 - player_id
        opponent = simulated.state.players[opponent_id]
        if opponent.has_rerolled:
            simulated.state.phase = GamePhase.ACTION
            simulated.state.current_player = 0
        else:
            simulated.state.current_player = opponent_id

        result.append(ChanceOutcome(simulated, probability))
    return result


def _game_with_dice(game: Game, player_id: int, dice_pool: DicePool) -> Game:
    """指定プレイヤーのダイスだけを差し替えた独立Gameを生成する。"""
    simulated = copy_game(game)
    simulated.state.players[player_id].dice = dice_pool
    simulated.state.players[player_id].has_rerolled = False
    return simulated
