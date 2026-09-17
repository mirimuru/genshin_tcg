from engine.cards import TalentCardDefinition
from engine.dice import DiceType
from engine.events import ElementalSkillEvent
from engine.statuses import EquipmentStatusDefinition, StatusInstance


class ColdBloodedStrikeStatus(EquipmentStatusDefinition):
    """冷血の剣。ガイアの元素スキル後、このラウンド1回だけ2HP回復する。"""

    status_id = "cold_blooded_strike"
    name = "冷血の剣"
    equipment_slot = "talent"

    def on_event(self, instance, event, game, context):
        if not isinstance(event, ElementalSkillEvent) or not event.resolved:
            return
        if event.player_id != context.owner_id or event.character_index != context.character_index:
            return
        if instance.data.get("last_heal_round") == game.state.round_number:
            return
        game.state.players[context.owner_id].characters[context.character_index].heal(2)
        instance.data["last_heal_round"] = game.state.round_number


class ColdBloodedStrike(TalentCardDefinition):
    """ガイア専用天賦カード「冷血の剣」。"""

    card_id = "cold_blooded_strike"
    name = "冷血の剣"
    cost = {DiceType.CRYO: 4}
    required_character_id = "kaeya"

    def create_status(self):
        return StatusInstance(ColdBloodedStrikeStatus)

    def play(self, game, player_id: int, target=None):
        super().play(game, player_id, target)
        game.elemental_skill(player_id)


COLD_BLOODED_STRIKE = ColdBloodedStrike()


__all__ = [
    "ColdBloodedStrike",
    "COLD_BLOODED_STRIKE",
    "ColdBloodedStrikeStatus",
]
