from collections.abc import Iterable

from engine.state import CharacterDefinition as _StateCharacterDefinition


class CharacterDefinition(_StateCharacterDefinition):
    """キャラクターDefinitionの公開API。"""

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
