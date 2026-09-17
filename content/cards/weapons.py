from engine.cards import WeaponCardDefinition
from engine.dice import DiceType
from engine.events import NormalAttackEvent
from engine.statuses import StatusInstance, WeaponEquipmentStatusDefinition


class TravelersHandySwordStatus(WeaponEquipmentStatusDefinition):
    """旅道の剣。装備キャラクターの与えるダメージを1増加させる。"""

    status_id = "travelers_handy_sword"
    name = "旅道の剣"
    weapon_type = "sword"

    def on_event(self, instance, event, game, context):
        if isinstance(event, NormalAttackEvent) and event.player_id == context.owner_id and not event.resolved:
            instance.data["armed"] = True

    def modify_damage(self, instance, amount, element, game, context):
        if instance.data.pop("armed", False):
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
