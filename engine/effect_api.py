from __future__ import annotations

from engine.statuses import StatusInstance
from engine.summons import SummonInstance


def add_character_status(game, player_id: int, character_index: int, status: StatusInstance) -> StatusInstance:
    """指定キャラクターへCharacter Statusを追加する。"""
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    player = game.state.players[player_id]
    if not 0 <= character_index < len(player.characters):
        raise ValueError("character_indexが不正です")
    if not isinstance(status, StatusInstance):
        raise TypeError("状態はStatusInstanceである必要があります")
    return player.characters[character_index].add_status(status)


def add_combat_status(game, player_id: int, status: StatusInstance) -> StatusInstance:
    """指定プレイヤーへCombat Statusを追加する。"""
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    if not isinstance(status, StatusInstance):
        raise TypeError("状態はStatusInstanceである必要があります")
    return game.state.players[player_id].add_combat_status(status)


def add_summon(game, player_id: int, summon: SummonInstance) -> SummonInstance:
    """指定プレイヤーへSummonを追加する。"""
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    if not isinstance(summon, SummonInstance):
        raise TypeError("召喚物はSummonInstanceである必要があります")
    return game.state.players[player_id].add_summon(summon)


def install(game_class) -> None:
    """Gameへ共通Effect APIを追加する。"""
    game_class.add_character_status = add_character_status
    game_class.add_combat_status = add_combat_status
    game_class.add_summon = add_summon
