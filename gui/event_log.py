"""ゲームイベントを人間が追跡しやすいログへ変換する。"""

from datetime import datetime

from engine.events import (
    CardActionEvent,
    CharacterSwitchEvent,
    DamageEvent,
    ElementalBurstEvent,
    ElementalSkillEvent,
    EnergyEvent,
    GameEvent,
    NormalAttackEvent,
    RoundEndEvent,
)


class EventLog:
    def __init__(self, max_entries: int = 500):
        self.max_entries = max_entries
        self.entries: list[str] = []

    def clear(self) -> None:
        self.entries.clear()

    def record(self, event: GameEvent) -> str:
        text = self._format(event)
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            del self.entries[:-self.max_entries]
        return entry

    @staticmethod
    def _format(event: GameEvent) -> str:
        player = lambda i: f"P{i + 1}"
        if isinstance(event, NormalAttackEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Character {event.character_index + 1} Normal Attack ({phase})"
        if isinstance(event, ElementalSkillEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Character {event.character_index + 1} Elemental Skill ({phase})"
        if isinstance(event, ElementalBurstEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Character {event.character_index + 1} Elemental Burst ({phase})"
        if isinstance(event, CharacterSwitchEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Switch Character {event.from_index + 1} -> {event.to_index + 1} ({phase})"
        if isinstance(event, CardActionEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Card {event.card_id} target={event.target!r} ({phase})"
        if isinstance(event, DamageEvent):
            reaction = f" reaction={event.reaction.value}" if event.reaction else ""
            phase = "resolved" if event.resolved else "pending"
            return f"{player(event.attacker_id)} -> P{event.target_id + 1}: {event.amount} {event.element.value} Damage{reaction} ({phase})"
        if isinstance(event, EnergyEvent):
            phase = "解決" if event.resolved else "開始"
            return f"{player(event.player_id)} Character {event.character_index + 1} Energy {event.amount:+d} ({event.reason}, {phase})"
        if isinstance(event, RoundEndEvent):
            return f"{player(event.player_id)} Round End"
        return type(event).__name__
