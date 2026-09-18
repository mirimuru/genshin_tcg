from engine.actions import ActionType
from engine.cards import WeaponCardDefinition
from engine.dice import DiceType
from engine.events import ElementalSkillEvent, NormalAttackEvent, ElementalBurstEvent
from engine.statuses import StatusInstance, WeaponEquipmentStatusDefinition


class _BasicWeaponStatus(WeaponEquipmentStatusDefinition):
    """通常攻撃のダメージを+1する標準武器状態。"""

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


class TravelerHandySwordStatus(_BasicWeaponStatus):
    """旅道の剣。"""

    status_id = "traveler_handy_sword"
    name = "旅道の剣"
    weapon_type = "sword"


class WhiteIronGreatswordStatus(_BasicWeaponStatus):
    """白鉄の大剣。"""

    status_id = "white_iron_greatsword"
    name = "白鉄の大剣"
    weapon_type = "claymore"


class WhiteTasselStatus(_BasicWeaponStatus):
    """白纓槍。"""

    status_id = "white_tassel"
    name = "白纓槍"
    weapon_type = "polearm"


class RavenBowStatus(_BasicWeaponStatus):
    """鴉羽の弓。"""

    status_id = "raven_bow"
    name = "鴉羽の弓"
    weapon_type = "bow"


class MagicGuideStatus(_BasicWeaponStatus):
    """魔導緒論。"""

    status_id = "magic_guide"
    name = "魔導緒論"
    weapon_type = "catalyst"


class SacrificialSwordStatus(WeaponEquipmentStatusDefinition):
    """祭礼の剣。元素スキル後、同キャラクターの次の攻撃系Actionを1ダイス軽減する。"""

    status_id = "sacrificial_sword"
    name = "祭礼の剣"
    weapon_type = "sword"

    def on_event(self, instance, event, game, context):
        if (
            isinstance(event, ElementalSkillEvent)
            and event.resolved
            and event.player_id == context.owner_id
            and event.character_index == context.character_index
        ):
            instance.data["next_action_discount"] = True
        elif (
            instance.data.get("next_action_discount", False)
            and event.player_id == context.owner_id
            and event.character_index == context.character_index
            and not event.resolved
            and isinstance(event, (NormalAttackEvent, ElementalSkillEvent, ElementalBurstEvent))
        ):
            instance.data["next_action_discount"] = False

    def modify_action_cost(self, instance, action, cost, game, context):
        if not instance.data.get("next_action_discount", False):
            return cost
        if action.player_id != context.owner_id:
            return cost
        if action.action_type not in {
            ActionType.NORMAL_ATTACK,
            ActionType.ELEMENTAL_SKILL,
            ActionType.ELEMENTAL_BURST,
        }:
            return cost
        modified = dict(cost)
        for dice_type, amount in modified.items():
            if dice_type is not DiceType.ANY and amount > 0:
                modified[dice_type] = amount - 1
                break
        return modified


class _BasicWeaponCard(WeaponCardDefinition):
    """通常攻撃+1型の星3武器カード共通実装。"""

    def create_status(self):
        return StatusInstance(self.status_definition)


class TravelerHandySword(_BasicWeaponCard):
    card_id = "traveler_handy_sword"
    name = "旅道の剣"
    cost = {DiceType.ANY: 2}
    weapon_type = "sword"
    status_definition = TravelerHandySwordStatus


class WhiteIronGreatsword(_BasicWeaponCard):
    card_id = "white_iron_greatsword"
    name = "白鉄の大剣"
    cost = {DiceType.ANY: 2}
    weapon_type = "claymore"
    status_definition = WhiteIronGreatswordStatus


class WhiteTassel(_BasicWeaponCard):
    card_id = "white_tassel"
    name = "白纓槍"
    cost = {DiceType.ANY: 2}
    weapon_type = "polearm"
    status_definition = WhiteTasselStatus


class RavenBow(_BasicWeaponCard):
    card_id = "raven_bow"
    name = "鴉羽の弓"
    cost = {DiceType.ANY: 2}
    weapon_type = "bow"
    status_definition = RavenBowStatus


class MagicGuide(_BasicWeaponCard):
    card_id = "magic_guide"
    name = "魔導緒論"
    cost = {DiceType.ANY: 2}
    weapon_type = "catalyst"
    status_definition = MagicGuideStatus


class SacrificialSword(_BasicWeaponCard):
    card_id = "sacrificial_sword"
    name = "祭礼の剣"
    cost = {DiceType.ANY: 3}
    weapon_type = "sword"
    status_definition = SacrificialSwordStatus


TRAVELER_HANDY_SWORD = TravelerHandySword()
WHITE_IRON_GREATSWORD = WhiteIronGreatsword()
WHITE_TASSEL = WhiteTassel()
RAVEN_BOW = RavenBow()
MAGIC_GUIDE = MagicGuide()
SACRIFICIAL_SWORD = SacrificialSword()


__all__ = [
    "TravelerHandySword",
    "TRAVELER_HANDY_SWORD",
    "TravelerHandySwordStatus",
    "WhiteIronGreatsword",
    "WHITE_IRON_GREATSWORD",
    "WhiteIronGreatswordStatus",
    "WhiteTassel",
    "WHITE_TASSEL",
    "WhiteTasselStatus",
    "RavenBow",
    "RAVEN_BOW",
    "RavenBowStatus",
    "MagicGuide",
    "MAGIC_GUIDE",
    "MagicGuideStatus",
    "SacrificialSword",
    "SACRIFICIAL_SWORD",
    "SacrificialSwordStatus",
]
