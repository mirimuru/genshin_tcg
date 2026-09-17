from engine.cards import ArtifactCardDefinition
from engine.dice import DiceType
from engine.events import DamageEvent, RoundEndEvent
from engine.state import Element
from engine.statuses import ArtifactEquipmentStatusDefinition, StatusInstance


class InstructorsCapStatus(ArtifactEquipmentStatusDefinition):
    """教官の帽子。装備者が元素反応を起こすと同元素ダイスを生成する。"""

    status_id = "instructors_cap"
    name = "教官の帽子"

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent):
            instance.data["triggers"] = 0
            return
        if not isinstance(event, DamageEvent) or not event.resolved:
            return
        if event.attacker_id != context.owner_id or context.character_index is None:
            return
        if context.character_index != game.state.players[event.attacker_id].active_character_index:
            return
        if event.reaction is None:
            return
        triggers = instance.data.get("triggers", 0)
        if triggers >= 3:
            return
        dice_type = {
            Element.PYRO: DiceType.PYRO,
            Element.HYDRO: DiceType.HYDRO,
            Element.ANEMO: DiceType.ANEMO,
            Element.ELECTRO: DiceType.ELECTRO,
            Element.DENDRO: DiceType.DENDRO,
            Element.CRYO: DiceType.CRYO,
            Element.GEO: DiceType.GEO,
        }.get(game.state.players[event.attacker_id].active_character.element)
        if dice_type is None:
            return
        game.state.players[event.attacker_id].dice.add(dice_type)
        instance.data["triggers"] = triggers + 1


class InstructorsCap(ArtifactCardDefinition):
    """聖遺物カード「教官の帽子」。"""

    card_id = "instructors_cap"
    name = "教官の帽子"
    cost = {DiceType.ANY: 2}

    def create_status(self):
        return StatusInstance(InstructorsCapStatus)


INSTRUCTORS_CAP = InstructorsCap()

__all__ = ["InstructorsCap", "INSTRUCTORS_CAP", "InstructorsCapStatus"]
