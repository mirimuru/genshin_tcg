import random
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
    ROLLABLE_DICE_TYPES = (
        DiceType.OMNI,
        DiceType.PYRO,
        DiceType.HYDRO,
        DiceType.ANEMO,
        DiceType.ELECTRO,
        DiceType.DENDRO,
        DiceType.CRYO,
        DiceType.GEO,
    )

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

    @classmethod
    def roll(cls, rng: random.Random | None = None, count: int = DEFAULT_DICE) -> "DicePool":
        """元素7種と万能から指定個数のダイスをランダム生成する。"""
        if count < 0:
            raise ValueError("dice count must not be negative")

        chooser = rng if rng is not None else random
        rolled = Counter(chooser.choice(cls.ROLLABLE_DICE_TYPES) for _ in range(count))
        return cls(rolled)

    @property
    def total(self) -> int:
        return sum(self._dice.values())

    def count(self, dice_type: DiceType) -> int:
        return self._dice[dice_type]

    def as_list(self) -> list[DiceType]:
        """現在のダイスを個々の要素として列挙する。"""
        return [dice_type for dice_type in self.ROLLABLE_DICE_TYPES for _ in range(self._dice[dice_type])]

    def reroll(self, selected: Mapping[DiceType, int], rng: random.Random | None = None) -> None:
        """指定したダイスだけを1回分ランダムに振り直す。"""
        selected_counter = Counter(selected)
        if any(not isinstance(dice_type, DiceType) for dice_type in selected_counter):
            raise TypeError("selected dice must be DiceType values")
        if any(count < 0 for count in selected_counter.values()):
            raise ValueError("selected dice count must not be negative")
        if DiceType.ANY in selected_counter:
            raise ValueError("任意ダイスはリロール対象にできません")
        if any(self._dice[dice_type] < count for dice_type, count in selected_counter.items()):
            raise ValueError("選択したダイスが所持数を超えています")

        for dice_type, count in selected_counter.items():
            self._dice[dice_type] -= count

        chooser = rng if rng is not None else random
        for _ in range(sum(selected_counter.values())):
            self._dice[chooser.choice(self.ROLLABLE_DICE_TYPES)] += 1
        self._remove_zeroes()

    def harmonize(self, source: DiceType, target: DiceType) -> None:
        """不要な元素ダイス1個を、指定した元素ダイス1個へ変換する。"""
        if source is DiceType.OMNI or target is DiceType.OMNI:
            raise ValueError("万能ダイスは調和の変換対象にできません")
        if source is DiceType.ANY or target is DiceType.ANY:
            raise ValueError("任意ダイスは調和の変換対象にできません")
        if source is target:
            raise ValueError("同じ元素への調和はできません")
        if self._dice[source] <= 0:
            raise ValueError("調和元のダイスがありません")

        self._dice[source] -= 1
        self._dice[target] += 1
        self._remove_zeroes()

    def can_pay(self, cost: Mapping[DiceType, int]) -> bool:
        """指定コストを現在のダイスだけで支払えるか判定する。"""
        if any(count < 0 for count in cost.values()):
            raise ValueError("dice cost must not be negative")

        remaining = Counter(self._dice)

        explicit_omni = cost.get(DiceType.OMNI, 0)
        if remaining[DiceType.OMNI] < explicit_omni:
            return False
        remaining[DiceType.OMNI] -= explicit_omni

        missing = 0
        for dice_type, required in cost.items():
            if dice_type in (DiceType.OMNI, DiceType.ANY):
                continue
            use = min(remaining[dice_type], required)
            remaining[dice_type] -= use
            missing += required - use

        if missing > remaining[DiceType.OMNI]:
            return False
        remaining[DiceType.OMNI] -= missing

        any_required = cost.get(DiceType.ANY, 0)
        return sum(remaining.values()) >= any_required

    def pay(self, cost: Mapping[DiceType, int]) -> None:
        """コストを支払い、ダイスを減らす。不足時は状態を変更せず例外を送出する。"""
        if not self.can_pay(cost):
            raise ValueError("ダイスが不足しています")

        remaining_cost = Counter(cost)

        for dice_type, required in list(remaining_cost.items()):
            if dice_type in (DiceType.OMNI, DiceType.ANY):
                continue
            direct = min(self._dice[dice_type], required)
            self._dice[dice_type] -= direct
            remaining_cost[dice_type] -= direct

        for dice_type, required in list(remaining_cost.items()):
            if dice_type in (DiceType.OMNI, DiceType.ANY) or required <= 0:
                continue
            self._dice[DiceType.OMNI] -= required
            remaining_cost[dice_type] = 0

        explicit_omni = remaining_cost[DiceType.OMNI]
        if explicit_omni:
            self._dice[DiceType.OMNI] -= explicit_omni

        any_required = remaining_cost[DiceType.ANY]
        if any_required:
            for dice_type in list(self._dice):
                if any_required == 0:
                    break
                use = min(self._dice[dice_type], any_required)
                self._dice[dice_type] -= use
                any_required -= use

        self._remove_zeroes()

    def _remove_zeroes(self) -> None:
        for dice_type in list(self._dice):
            if self._dice[dice_type] <= 0:
                del self._dice[dice_type]

    def reset_to_default(self) -> None:
        self._dice.clear()
        self._dice[DiceType.OMNI] = self.DEFAULT_DICE
