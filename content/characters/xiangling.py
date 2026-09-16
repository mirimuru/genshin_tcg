from engine.characters import CharacterDefinition
from engine.dice import DiceType
from engine.events import ElementalBurstEvent, ElementalSkillEvent, RoundEndEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance
from engine.summons import SummonDefinition, SummonInstance


class Guoba(SummonDefinition):
    summon_id = "guoba"
    name = "グゥオパァー"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            game.deal_damage(context.owner_id, 1 - context.owner_id, 2, Element.PYRO)
            instance.consume()


class Pyronado(SummonDefinition):
    summon_id = "pyronado"
    name = "旋火輪"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if isinstance(event, ElementalSkillEvent) and event.player_id == context.owner_id and event.resolved:
            game.deal_damage(context.owner_id, 1 - context.owner_id, 2, Element.PYRO)
            instance.consume()


class XianglingActionTrigger(StatusDefinition):
    status_id = "xiangling_action_trigger"
    name = "香菱固有効果"
    max_usages = None

    def on_event(self, instance, event, game, context):
        if context.character_index is None:
            return
        if event.player_id != context.owner_id or event.character_index != context.character_index:
            return
        player = game.state.players[context.owner_id]
        if isinstance(event, ElementalSkillEvent) and event.resolved:
            player.add_summon(SummonInstance(Guoba))
        elif isinstance(event, ElementalBurstEvent) and event.resolved:
            player.add_summon(SummonInstance(Pyronado))


class Xiangling(CharacterDefinition):
    character_id = "xiangling"
    name = "香菱"
    element = Element.PYRO
    max_hp = 10
    max_energy = 2
    normal_attack_cost = {DiceType.PYRO: 1, DiceType.ANY: 2}
    elemental_skill_cost = {DiceType.PYRO: 3}
    elemental_burst_cost = {DiceType.PYRO: 4}

    def create_state(self):
        state = super().create_state()
        state.add_status(StatusInstance(XianglingActionTrigger))
        return state

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        pass

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 3, Element.PYRO)


XIANG_LING = Xiangling()
