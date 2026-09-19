from engine.characters import CharacterDefinition
from engine.dice import DiceType
from engine.events import ElementalBurstEvent, ElementalSkillEvent, NormalAttackEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance


RAIN_SWORD_ID = "rain_sword"


class RainSword(StatusDefinition):
    status_id = RAIN_SWORD_ID
    name = "雨すだれの剣"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if not isinstance(event, NormalAttackEvent):
            return
        if event.player_id != context.owner_id or not event.resolved:
            return
        game.deal_damage(context.owner_id, 1 - context.owner_id, 2, Element.HYDRO)
        instance.consume()


class Xingqiu(CharacterDefinition):
    character_id = "xingqiu"
    name = "行秋"
    element = Element.HYDRO
    max_hp = 10
    max_energy = 2
    weapon_type = "sword"
    normal_attack_cost = {DiceType.HYDRO: 1, DiceType.ANY: 2}
    elemental_skill_cost = {DiceType.HYDRO: 3}
    elemental_burst_cost = {DiceType.HYDRO: 2}

    @staticmethod
    def rain_sword() -> StatusInstance:
        return StatusInstance(RainSword)

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.HYDRO)
        game.state.players[player_id].add_combat_status(self.rain_sword())

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 1, Element.HYDRO)
        game.state.players[player_id].add_combat_status(self.rain_sword())


XINGQIU = Xingqiu()
