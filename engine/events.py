from dataclasses import dataclass

from engine.elemental_reactions import ElementalReaction
from engine.state import Element


class GameEvent:
    """ゲーム内の効果が購読できるイベントの基底クラス。"""


@dataclass
class CharacterActionEvent(GameEvent):
    """キャラクターアクションの開始・解決を表す基底イベント。"""
    player_id: int
    character_index: int
    resolved: bool = False


@dataclass
class NormalAttackEvent(CharacterActionEvent):
    """通常攻撃の開始・解決イベント。"""


@dataclass
class ElementalSkillEvent(CharacterActionEvent):
    """元素スキルの開始・解決イベント。"""


@dataclass
class ElementalBurstEvent(CharacterActionEvent):
    """元素爆発の開始・解決イベント。"""


@dataclass
class CharacterSwitchEvent(GameEvent):
    """キャラクター切り替えの開始・解決イベント。"""
    player_id: int
    from_index: int
    to_index: int
    resolved: bool = False


@dataclass
class CardActionEvent(GameEvent):
    """カード使用の開始・解決を表すイベント。"""
    player_id: int
    card_id: str
    target: object = None
    resolved: bool = False


@dataclass
class DamageEvent(GameEvent):
    attacker_id: int
    target_id: int
    amount: int
    element: Element
    reaction: ElementalReaction | None = None
    resolved: bool = False


@dataclass
class EnergyEvent(GameEvent):
    """キャラクターのEnergy変更を表すイベント。"""
    player_id: int
    character_index: int
    amount: int
    reason: str
    resolved: bool = False


@dataclass
class RoundEndEvent(GameEvent):
    player_id: int


@dataclass(frozen=True)
class EffectContext:
    owner_id: int
    character_index: int | None = None
