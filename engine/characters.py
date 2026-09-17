from collections.abc import Iterable

from engine.state import CharacterDefinition as _StateCharacterDefinition


class CharacterDefinition(_StateCharacterDefinition):
    """キャラクターDefinitionの公開API。

    サブクラスではクラス属性としてメタデータを定義できるようにし、
    ``DILUC = Diluc()`` のように引数なしで生成できる。
    明示的な引数を渡した場合は通常のCharacterDefinitionとして初期化する。
    """

    character_id = ""
    name = ""
    element = None
    max_hp = 10
    max_energy = 2
    weapon_type = None

    def __init__(
        self,
        character_id: str | None = None,
        name: str | None = None,
        element=None,
        max_hp: int | None = None,
        max_energy: int | None = None,
        weapon_type: str | None = None,
    ):
        super().__init__(
            character_id=self.character_id if character_id is None else character_id,
            name=self.name if name is None else name,
            element=self.element if element is None else element,
            max_hp=self.max_hp if max_hp is None else max_hp,
            max_energy=self.max_energy if max_energy is None else max_energy,
            weapon_type=self.weapon_type if weapon_type is None else weapon_type,
        )

    def create_state(self):
        from engine.state import CharacterState

        return CharacterState(
            name=self.name,
            element=self.element,
            max_hp=self.max_hp,
            max_energy=self.max_energy,
            definition=self,
        )


class CharacterRegistry:
    """キャラクターIDからCharacterDefinitionを解決するRegistry。"""

    def __init__(self, definitions: Iterable[CharacterDefinition] | None = None):
        self._definitions: dict[str, CharacterDefinition] = {}
        for definition in definitions or ():
            self.register(definition)

    def register(self, definition: CharacterDefinition) -> CharacterDefinition:
        if not isinstance(definition, CharacterDefinition):
            raise TypeError("キャラクター定義はCharacterDefinitionである必要があります")
        if not getattr(definition, "character_id", ""):
            raise ValueError("character_id must not be empty")
        if definition.character_id in self._definitions:
            raise ValueError(f"キャラクターIDが重複しています: {definition.character_id}")
        self._definitions[definition.character_id] = definition
        return definition

    def get(self, character_id: str) -> CharacterDefinition:
        try:
            return self._definitions[character_id]
        except KeyError as exc:
            raise ValueError(f"未登録のキャラクターです: {character_id}") from exc

    def contains(self, character_id: str) -> bool:
        return character_id in self._definitions

    def __iter__(self):
        return iter(self._definitions.values())
