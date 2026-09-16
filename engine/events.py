from dataclasses import dataclass

from engine.elemental_reactions import ElementalReaction
from engine.state import Element


class GameEvent:
    """ゲーム内の効果が購読できるイベントの基底クラス。"""


@dataclass
class DamageEvent(GameEvent):
    attacker_id: int
    target_id: int
    amount: int
    element: Element
    reaction: ElementalReaction | None = None
    resolved: bool = False


@dataclass
class RoundEndEvent(GameEvent):
    player_id: int


@dataclass(frozen=True)
class EffectContext:
    owner_id: int
    character_index: int | None = None
