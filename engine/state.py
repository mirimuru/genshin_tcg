from enum import Enum
from typing import Iterable, List, Optional

from engine.dice import DicePool
from engine.statuses import EquipmentStatusDefinition, StatusInstance
from engine.summons import SummonInstance


class Element(Enum):
    PYRO = "炎"
    HYDRO = "水"
    ANEMO = "風"
    ELECTRO = "雷"
    DENDRO = "草"
    CRYO = "氷"
    GEO = "岩"
    PHYSICAL = "物理"


class GamePhase(Enum):
    ROLL = "roll"
    ACTION = "action"


class CharacterDefinition:
    """キャラクター固有ルールと固定情報を保持する定義。"""

    def __init__(self, character_id: str, name: str, element: Element, max_hp: int = 10, max_energy: int = 2):
        if not character_id:
            raise ValueError("character_id must not be empty")
        if not name:
            raise ValueError("name must not be empty")
        if max_hp <= 0:
            raise ValueError("max_hp must be greater than 0")
        if max_energy < 0:
            raise ValueError("max_energy must not be negative")
        self.character_id = character_id
        self.name = name
        self.element = element
        self.max_hp = max_hp
        self.max_energy = max_energy

    def create_state(self):
        return CharacterState(
            name=self.name,
            element=self.element,
            max_hp=self.max_hp,
            max_energy=self.max_energy,
            definition=self,
        )

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 3, self.element)

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 4, self.element)


class CharacterRegistry:
    """キャラクターIDからCharacterDefinitionを解決するRegistry。"""

    def __init__(self, definitions: Iterable[CharacterDefinition] | None = None):
        self._definitions: dict[str, CharacterDefinition] = {}
        for definition in definitions or ():
            self.register(definition)

    def register(self, definition: CharacterDefinition) -> CharacterDefinition:
        if not isinstance(definition, CharacterDefinition):
            raise TypeError("キャラクター定義はCharacterDefinitionである必要があります")
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


class CharacterState:
    def __init__(self, name: str, element: Element, max_hp: int = 10, max_energy: int = 2, definition: Optional[CharacterDefinition] = None):
        if definition is not None:
            if not isinstance(definition, CharacterDefinition):
                raise TypeError("definitionはCharacterDefinitionである必要があります")
            name, element, max_hp, max_energy = definition.name, definition.element, definition.max_hp, definition.max_energy
        else:
            definition = CharacterDefinition(f"legacy:{name}", name, element, max_hp, max_energy)
        self.definition = definition
        self.name = name
        self.element = element
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_energy = max_energy
        self.energy = 0
        self.elemental_aura: Optional[Element] = None
        self.statuses: List[StatusInstance] = []

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def defeated(self) -> bool:
        return not self.alive

    def receive_damage(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("damage amount must not be negative")
        old_hp = self.hp
        self.hp = max(0, self.hp - amount)
        return old_hp - self.hp

    def heal(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("damage amount must not be negative")
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def add_status(self, status: StatusInstance) -> StatusInstance:
        if not isinstance(status, StatusInstance): raise TypeError("状態はStatusInstanceである必要があります")
        self.remove_status(status.status_id); self.statuses.append(status); return status

    def add_equipment(self, status: StatusInstance) -> StatusInstance:
        """装備状態を装備スロット単位で置き換えてキャラクターへ装着する。"""
        if not isinstance(status, StatusInstance):
            raise TypeError("装備はStatusInstanceである必要があります")
        if not isinstance(status.definition, EquipmentStatusDefinition):
            raise TypeError("装備にはEquipmentStatusDefinitionが必要です")
        if not status.definition.equipment_slot:
            raise ValueError("equipment_slotは空にできません")
        self.statuses[:] = [
            current
            for current in self.statuses
            if not (
                isinstance(current.definition, EquipmentStatusDefinition)
                and current.definition.equipment_slot == status.definition.equipment_slot
            )
        ]
        self.statuses.append(status)
        return status

    def get_status(self, status_id: str) -> Optional[StatusInstance]:
        return next((s for s in self.statuses if s.status_id == status_id), None)

    def has_status(self, status_id: str) -> bool: return self.get_status(status_id) is not None

    def remove_status(self, status_id: str) -> Optional[StatusInstance]:
        for i, status in enumerate(self.statuses):
            if status.status_id == status_id: return self.statuses.pop(i)
        return None

    def remove_expired_statuses(self) -> None:
        self.statuses[:] = [s for s in self.statuses if not s.expired]


class PlayerState:
    def __init__(self, player_id: int, characters: List[CharacterState]):
        if len(characters) != 3: raise ValueError("七聖召喚ではキャラクターを3体指定してください")
        self.player_id = player_id; self.characters = characters; self.active_character_index = 0
        self.dice = DicePool.default(); self.hand = []; self.deck = []
        self.summons: dict[str, SummonInstance] = {}; self.combat_statuses: List[StatusInstance] = []
        self.has_ended_round = False; self.has_rerolled = False; self.must_switch = False; self.shield = 0

    @property
    def active_character(self): return self.characters[self.active_character_index]
    @property
    def defeated(self): return all(not c.alive for c in self.characters)
    @property
    def requires_switch(self): return (self.must_switch or not self.active_character.alive) and not self.defeated

    def add_shield(self, amount):
        if amount < 0: raise ValueError("shield amount must not be negative")
        old = self.shield; self.shield = min(2, self.shield + amount); return self.shield - old
    def take_damage(self, amount, *, ignore_shield=False):
        if amount < 0: raise ValueError("damage amount must not be negative")
        if ignore_shield or self.shield <= 0: return self.active_character.receive_damage(amount)
        absorbed = min(self.shield, amount); self.shield -= absorbed; return self.active_character.receive_damage(amount - absorbed)
    def add_combat_status(self, status):
        if not isinstance(status, StatusInstance): raise TypeError("状態はStatusInstanceである必要があります")
        self.remove_combat_status(status.status_id); self.combat_statuses.append(status); return status
    def get_combat_status(self, status_id): return next((s for s in self.combat_statuses if s.status_id == status_id), None)
    def has_combat_status(self, status_id): return self.get_combat_status(status_id) is not None
    def remove_combat_status(self, status_id):
        for i, status in enumerate(self.combat_statuses):
            if status.status_id == status_id: return self.combat_statuses.pop(i)
        return None
    def remove_expired_combat_statuses(self): self.combat_statuses[:] = [s for s in self.combat_statuses if not s.expired]
    def add_summon(self, summon):
        if not isinstance(summon, SummonInstance): raise TypeError("召喚物はSummonInstanceである必要があります")
        self.summons[summon.summon_id] = summon; return summon
    def get_summon(self, summon_id):
        summon = self.summons.get(summon_id); return summon if isinstance(summon, SummonInstance) else None
    def has_summon(self, summon_id): return self.get_summon(summon_id) is not None
    def remove_summon(self, summon_id): return self.summons.pop(summon_id, None)
    def remove_expired_summons(self): self.summons = {i:s for i,s in self.summons.items() if not s.expired}
    def can_switch_to(self, index): return 0 <= index < len(self.characters) and index != self.active_character_index and self.characters[index].alive
    def switch_character(self, index):
        if not isinstance(index, int) or index < 0 or index >= len(self.characters):
            raise ValueError("存在しないキャラクターです")
        if index == self.active_character_index:
            raise ValueError("すでにアクティブなキャラクターです")
        if not self.characters[index].alive:
            raise ValueError("戦闘不能のキャラクターには交代できません")
        self.active_character_index = index
    def alive_character_indices(self): return [i for i,c in enumerate(self.characters) if c.alive]


class GameState:
    def __init__(self, players):
        if len(players) != 2: raise ValueError("プレイヤーは2人必要です")
        self.players = players; self.round_number = 1; self.phase = GamePhase.ROLL; self.current_player = 0; self.game_over = False; self.winner = None; self.check_game_over()
    def opponent_of(self, player_id):
        if player_id not in (0,1): raise ValueError("player_id must be 0 or 1")
        return self.players[1-player_id]
    def check_game_over(self):
        defeated = [p.player_id for p in self.players if p.defeated]; self.game_over = bool(defeated); self.winner = 1-defeated[0] if len(defeated)==1 else None; return self.game_over
