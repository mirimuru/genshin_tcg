from engine.cards import WeaponCardDefinition
from engine.dice import DiceType
from engine.events import CharacterActionEvent
from engine.statuses import StatusInstance, WeaponEquipmentStatusDefinition


class TravelersHandySwordStatus(WeaponEquipmentStatusDefinition):
    """旅道の剣。装備キャラクターの与えるダメージを1増加させる。"""

    status_id = "travelers_handy_sword"
    name = "旅道の剣"
    weapon_type = "sword"

    def on_event(self, instance, event, game, context):
        if not isinstance(event, CharacterActionEvent):
            return
        if event.player_id != context.owner_id or event.character_index != context.character_index:
            return
        instance.data["armed"] = not event.resolved

    def modify_damage(self, instance, amount, element, game, context):
        if instance.data.get("armed", False):
            return amount + 1, element
        return amount, element


class TravelersHandySword(WeaponCardDefinition):
    """武器カード「旅道の剣」。"""

    card_id = "travelers_handy_sword"
    name = "旅道の剣"
    cost = {DiceType.ANY: 2}
    weapon_type = "sword"

    def create_status(self):
        return StatusInstance(TravelersHandySwordStatus)


TRAVELERS_HANDY_SWORD = TravelersHandySword()


__all__ = [
    "TravelersHandySword",
    "TRAVELERS_HANDY_SWORD",
    "TravelersHandySwordStatus",
]
