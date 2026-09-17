from __future__ import annotations

from engine.state import GameState


# The values are intentionally small and interpretable. Terminal outcomes
# dominate every heuristic term so search can never prefer a non-terminal
# position over a win or a loss.
WIN_SCORE = 10000.0
HP_WEIGHT = 1.0
ALIVE_WEIGHT = 3.0
ENERGY_WEIGHT = 0.75
STATUS_USAGE_WEIGHT = 0.5
SUMMON_USAGE_WEIGHT = 0.75
HAND_WEIGHT = 0.5
DICE_WEIGHT = 0.25
SHIELD_WEIGHT = 0.75
AURA_WEIGHT = 0.25
ACTION_TEMPO_WEIGHT = 1.0
ENDED_ROUND_WEIGHT = 1.0


def _player_heuristic(game: GameState, player_id: int) -> float:
    player = game.players[player_id]
    score = 0.0

    score += sum(character.hp for character in player.characters) * HP_WEIGHT
    score += sum(character.alive for character in player.characters) * ALIVE_WEIGHT
    score += sum(character.energy for character in player.characters) * ENERGY_WEIGHT
    score += player.shield * SHIELD_WEIGHT
    score += len(player.hand) * HAND_WEIGHT
    score += player.dice.total * DICE_WEIGHT
    score -= player.has_ended_round * ENDED_ROUND_WEIGHT

    for character in player.characters:
        score += sum(
            (status.usages if status.usages is not None else 1)
            for status in character.statuses
        ) * STATUS_USAGE_WEIGHT
        if character.elemental_aura is not None:
            score += AURA_WEIGHT

    score += sum(
        (summon.usages if summon.usages is not None else 1)
        for summon in player.summons.values()
    ) * SUMMON_USAGE_WEIGHT

    return score


def evaluate_state(game: GameState, player_id: int) -> float:
    """ゲーム状態を指定プレイヤー視点のスカラー値へ変換する。

    正の値は指定プレイヤーに有利、負の値は相手に有利な状態を表す。
    この関数は状態を変更しないため、シミュレーション探索から直接利用できる。
    """
    if not isinstance(game, GameState):
        raise TypeError("game must be GameState")
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")

    opponent_id = 1 - player_id
    if game.game_over:
        if game.winner == player_id:
            return WIN_SCORE
        if game.winner == opponent_id:
            return -WIN_SCORE
        return 0.0

    score = _player_heuristic(game, player_id) - _player_heuristic(game, opponent_id)
    if game.current_player == player_id:
        score += ACTION_TEMPO_WEIGHT
    else:
        score -= ACTION_TEMPO_WEIGHT
    return score
