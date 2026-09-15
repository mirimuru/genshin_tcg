from dataclasses import dataclass
from enum import Enum
from typing import Optional

from engine.state import Element


class ElementalReaction(Enum):
    """七聖召喚で使用する元素反応。"""

    VAPORIZE = "蒸発"
    MELT = "溶解"
    ELECTRO_CHARGED = "感電"
    FROZEN = "凍結"
    SUPERCONDUCT = "超伝導"
    QUICKEN = "超激化"
    BURNING = "燃焼"
    OVERLOADED = "過負荷"
    BLOOM = "開花"
    SWIRL = "拡散"
    CRYSTALLIZE = "結晶"


@dataclass(frozen=True)
class ReactionResult:
    """元素反応判定の結果。

    現段階では反応種別のみを保持し、追加ダメージや状態効果は
    後続のダメージ・状態システムで扱う。
    """

    reaction: Optional[ElementalReaction]

    @property
    def occurred(self) -> bool:
        return self.reaction is not None


class ReactionResolver:
    """2つの元素から元素反応を判定する。"""

    _REACTIONS = {
        frozenset((Element.PYRO, Element.HYDRO)): ElementalReaction.VAPORIZE,
        frozenset((Element.PYRO, Element.CRYO)): ElementalReaction.MELT,
        frozenset((Element.HYDRO, Element.ELECTRO)): ElementalReaction.ELECTRO_CHARGED,
        frozenset((Element.HYDRO, Element.CRYO)): ElementalReaction.FROZEN,
        frozenset((Element.ELECTRO, Element.CRYO)): ElementalReaction.SUPERCONDUCT,
        frozenset((Element.ELECTRO, Element.DENDRO)): ElementalReaction.QUICKEN,
        frozenset((Element.PYRO, Element.DENDRO)): ElementalReaction.BURNING,
        frozenset((Element.PYRO, Element.ELECTRO)): ElementalReaction.OVERLOADED,
        frozenset((Element.HYDRO, Element.DENDRO)): ElementalReaction.BLOOM,
        frozenset((Element.ANEMO, Element.PYRO)): ElementalReaction.SWIRL,
        frozenset((Element.ANEMO, Element.HYDRO)): ElementalReaction.SWIRL,
        frozenset((Element.ANEMO, Element.ELECTRO)): ElementalReaction.SWIRL,
        frozenset((Element.ANEMO, Element.CRYO)): ElementalReaction.SWIRL,
        frozenset((Element.GEO, Element.PYRO)): ElementalReaction.CRYSTALLIZE,
        frozenset((Element.GEO, Element.HYDRO)): ElementalReaction.CRYSTALLIZE,
        frozenset((Element.GEO, Element.ELECTRO)): ElementalReaction.CRYSTALLIZE,
        frozenset((Element.GEO, Element.CRYO)): ElementalReaction.CRYSTALLIZE,
    }

    @classmethod
    def resolve(cls, first: Element, second: Element) -> ReactionResult:
        """2つの元素の組み合わせから反応を判定する。

        元素の順序は反応結果に影響しない。同元素や反応しない組み合わせは
        ``ReactionResult(reaction=None)`` を返す。
        """
        if not isinstance(first, Element) or not isinstance(second, Element):
            raise TypeError("first and second must be Element values")

        reaction = cls._REACTIONS.get(frozenset((first, second)))
        return ReactionResult(reaction=reaction)
