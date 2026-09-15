from collections import Counter
from enum import Enum
from typing import Mapping


class DiceType(Enum):
    OMNI = "万能"
    PYRO = "炎"
    HYDRO = "水"
    ANEMO = "風"
    ELECTRO = "雷"
    DENDRO = "草"
    CRYO = "氷"
    GEO = "岩"
    ANY = "任意"


class DicePool:
    """プレイヤーが所持しているダイスを管理する簡易プール。"""

    DEFAULT_DICE = 8

    def __init__(self, dice: Mapping[DiceType, int] | None = None):
        self._dice = Counter()
        if dice is not None:
            for dice_type, count in dice.items():
                if not isinstance(dice_type, DiceType):
                    raise TypeError("dice_type must be a DiceType")
                if count < 0:
                    raise ValueError("dice count must not be negative")
                if count:
                    self._dice[dice_type] = count

    @classmethod
    def default(cls) -> "DicePool":
        """現在の簡易ルール用の初期ダイス8個を生成する。"""
        return cls({DiceType.OMNI: cls.DEFAULT_DICE})

    @property
    def total(self) -> int:
        return sum(self._dice.values())

    def count(self, dice_type: DiceType) -> int:
        return self._dice[dice_type]

    def can_pay(self, cost: Mapping[DiceType, int]) -> bool:
        if any(count < 0 for count in cost.values()):
            raise ValueError("dice cost must not be negative")

        remaining = Counter(self._dice)
        omni = remaining[DiceType.OMNI]

        for dice_type, required in cost.items():
            if dice_type is DiceType.ANY:
                continue
            available = remaining[dice_type]
            use = min(available, required)
            remaining[dice_type] -= use
            required -= use
            if dice_type is not DiceType.OMNI:
                omni -= required
            else:
                omni -= required
            if omni < 0:
                return False

        any_required = cost.get(DiceType.ANY, 0)
        return remaining_total(remaining) - omni >= 0 and self.total >= sum(cost.values())

    def pay(self, cost: Mapping[DiceType, int]) -> None:
        if not self.can_pay(cost):
            raise ValueError("ダイスが不足しています")

        for dice_type, required in cost.items():
            if dice_type is DiceType.ANY:
                for available_type in list(self._dice):
                    if required == 0:
                        break
                    if available_type is DiceType.ANY:
                        continue
                    use = min(self._dice[available_type], required)
                    self._dice[available_type] -= use
                    required -= use
                continue

            direct = min(self._dice[dice_type], required)
            self._dice[dice_type] -= direct
            required -= direct
            if required:
                self._dice[DiceType.OMNI] -= required

        self._remove_zeroes()

    def _remove_zeroes(self) -> None:
        for dice_type in list(self._dice):
            if self._dice[dice_type] <= 0:
                del self._dice[dice_type]

    def reset_to_default(self) -> None:
        self._dice.clear()
        self._dice[DiceType.OMNI] = self.DEFAULT_DICE


def remaining_total(dice: Mapping[DiceType, int]) -> int:
    return sum(dice.values())
