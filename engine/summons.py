from __future__ import annotations

from abc import ABC
from collections.abc import Sequence


class SummonDefinition(ABC):
    """召喚物1種類の定義。"""

    summon_id = ""
    name = ""
    max_usages: int | None = None

    def on_event(self, instance, event, game, context) -> None:
        """イベントフック。必要な召喚物だけオーバーライドする。"""


class SummonInstance:
    """ゲーム中に存在する1つのSummonDefinitionの実体。"""

    def __init__(self, definition: type[SummonDefinition] | SummonDefinition, *, usages: int | None = None):
        self.definition = definition() if isinstance(definition, type) else definition
        if not isinstance(self.definition, SummonDefinition):
            raise TypeError("召喚物定義はSummonDefinitionまたはそのサブクラスである必要があります")
        if not self.definition.summon_id:
            raise ValueError("summon_idは空にできません")
        max_usages = self.definition.max_usages
        if max_usages is not None and max_usages < 0:
            raise ValueError("max_usages must not be negative")
        if usages is None:
            usages = max_usages
        if usages is not None and usages < 0:
            raise ValueError("usages must not be負です")
        if max_usages is not None and usages is not None and usages > max_usages:
            raise ValueError("usages cannot exceed max_usages")
        self.usages = usages

    @property
    def summon_id(self) -> str:
        return self.definition.summon_id

    @property
    def name(self) -> str:
        return self.definition.name

    def consume(self, amount: int = 1) -> int:
        if amount < 0:
            raise ValueError("consume amount must not be negative")
        if self.usages is None:
            return 0
        consumed = min(self.usages, amount)
        self.usages -= consumed
        return consumed

    @property
    def expired(self) -> bool:
        return self.usages == 0


class SummonRegistry:
    """召喚物IDから召喚物定義を解決するレジストリ。"""

    def __init__(self, definitions: Sequence[type[SummonDefinition] | SummonInstance | SummonDefinition] = ()):
        self._summons: dict[str, SummonDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: type[SummonDefinition] | SummonDefinition) -> None:
        summon = definition() if isinstance(definition, type) else definition
        if not isinstance(summon, SummonDefinition):
            raise TypeError("召喚物定義はSummonDefinitionまたはそのサブクラスである必要があります")
        if not summon.summon_id:
            raise ValueError("summon_idは空にできません")
        if summon.summon_id in self._summons:
            raise ValueError(f"召喚物IDが重複しています: {summon.summon_id}")
        self._summons[summon.summon_id] = summon

    def get(self, summon_id: str) -> SummonDefinition:
        try:
            return self._summons[summon_id]
        except KeyError as exc:
            raise ValueError(f"未登録の召喚物です: {summon_id}") from exc

    def create(self, summon_id: str, *, usages: int | None = None) -> SummonInstance:
        return SummonInstance(self.get(summon_id), usages=usages)

    def __contains__(self, summon_id: str) -> bool:
        return summon_id in self._summons

    def __iter__(self):
        return iter(self._summons.values())
