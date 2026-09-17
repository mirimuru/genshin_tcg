from engine.cards import WeaponCardDefinition
from engine.dice import DiceType
from engine.events import NormalAttackEvent
from engine.statuses import StatusInstance, WeaponEquipmentStatusDefinition


class TravelerHandySwordStatus(WeaponEquipmentStatusDefinition):
    """旅人の便利な剣。装備キャラクターの次の通常攻撃を+1する準備状態を持つ。"""

    status_id = "traveler_handy_sword"
    name = "旅人の便利な剣"
    equipment_slot = "weapon"
    weapon_type = "sword"

    def on_event(self, instance, event, game, context):
        if (
            isinstance(event, NormalAttackEvent)
            and event.player_id == context.owner_id
            and event.character_index == context.character_index
            and not event.resolved
        ):
            instance.data["armed"] = True

    def modify_damage(self, instance, amount, element, game, context):
        if instance.data.pop("armed", False):
            return amount + 1, element
        return amount, element


class TravelerHandySword(WeaponCardDefinition):
    """片手剣の武器カード。"""

    card_id = "traveler_handy_sword"
    name = "旅人の便利な剣"
    cost = {DiceType.ANY: 2}
    weapon_type = "sword"

    def create_status(self):
        return StatusInstance(TravelerHandySwordStatus)


TRAVELER_HANDY_SWORD = TravelerHandySword()


__all__ = [
    "TravelerHandySword",
    "TRAVELER_HANDY_SWORD",
    "TravelerHandySwordStatus",
]
