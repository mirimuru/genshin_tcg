from __future__ import annotations

from abc import ABC
from collections.abc import Sequence


class StatusDefinition(ABC):
    """状態効果1種類の定義。

    状態そのもののルールは定義クラスに、現在の残り回数などの可変値は
    ``StatusInstance`` に保持する。これにより同じ状態を複数のキャラクターや
    プレイヤーへ独立して付与できる。
    """

    status_id = ""
    name = ""
    max_usages: int | None = None


class StatusInstance:
    """ゲーム中に存在する1つのStatusDefinitionの実体。"""

    def __init__(
        self,
        definition: type[StatusDefinition] | StatusDefinition,
        *,
        usages: int | None = None,
    ):
        self.definition = (
            definition() if isinstance(definition, type) else definition
        )
        if not isinstance(self.definition, StatusDefinition):
            raise TypeError(
                "状態定義はStatusDefinitionまたはそのサブクラスである必要があります"
            )
        if not self.definition.status_id:
            raise ValueError("status_idは空にできません")

        max_usages = self.definition.max_usages
        if max_usages is not None and max_usages < 0:
            raise ValueError("max_usages must not be negative")
        if usages is None:
            usages = max_usages
        if usages is not None and usages < 0:
            raise ValueError("usages must not be negative")
        if max_usages is not None and usages is not None and usages > max_usages:
            raise ValueError("usages cannot exceed max_usages")

        self.usages = usages

    @property
    def status_id(self) -> str:
        return self.definition.status_id

    @property
    def name(self) -> str:
        return self.definition.name

    def consume(self, amount: int = 1) -> int:
        """指定回数を消費し、実際に消費した回数を返す。"""
        if amount < 0:
            raise ValueError("consume amount must not be negative")
        if self.usages is None:
            return 0

        consumed = min(self.usages, amount)
        self.usages -= consumed
        return consumed

    @property
    def expired(self) -> bool:
        """使用回数型状態が切れたかを返す。無期限状態はFalse。"""
        return self.usages == 0


class StatusRegistry:
    """状態IDから状態定義を解決するレジストリ。"""

    def __init__(
        self,
        definitions: Sequence[type[StatusDefinition] | StatusDefinition] = (),
    ):
        self._statuses: dict[str, StatusDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(
        self,
        definition: type[StatusDefinition] | StatusDefinition,
    ) -> None:
        status = definition() if isinstance(definition, type) else definition
        if not isinstance(status, StatusDefinition):
            raise TypeError(
                "状態定義はStatusDefinitionまたはそのサブクラスである必要があります"
            )
        if not status.status_id:
            raise ValueError("status_idは空にできません")
        if status.status_id in self._statuses:
            raise ValueError(f"状態IDが重複しています: {status.status_id}")
        self._statuses[status.status_id] = status

    def get(self, status_id: str) -> StatusDefinition:
        try:
            return self._statuses[status_id]
        except KeyError as exc:
            raise ValueError(f"未登録の状態です: {status_id}") from exc

    def create(self, status_id: str, *, usages: int | None = None) -> StatusInstance:
        return StatusInstance(self.get(status_id), usages=usages)

    def __contains__(self, status_id: str) -> bool:
        return status_id in self._statuses

    def __iter__(self):
        return iter(self._statuses.values())
