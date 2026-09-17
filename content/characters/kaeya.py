from engine.characters import CharacterDefinition
from engine.dice import DiceType
from engine.events import CharacterActionEvent, CharacterSwitchEvent, ElementalBurstEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance


class Icicle(StatusDefinition):
    status_id = "kaeya_icicle"
    name = "霜の舞"
    max_usages = 3

    def on_event(self, instance, event, game, context):
        if isinstance(event, CharacterSwitchEvent) and event.player_id == context.owner_id and event.resolved:
            game.deal_damage(context.owner_id, 1 - context.owner_id, 2, Element.CRYO)
            instance.consume()


class KaeyaActionTrigger(StatusDefinition):
    status_id = "kaeya_action_trigger"
    name = "ガイア固有効果"
    max_usages = None

    def on_event(self, instance, event, game, context):
        if not isinstance(event, CharacterActionEvent):
            return
        if event.player_id != context.owner_id or event.character_index != context.character_index:
            return
        if isinstance(event, ElementalBurstEvent) and event.resolved:
            game.state.players[context.owner_id].add_combat_status(StatusInstance(Icicle))


class Kaeya(CharacterDefinition):
    character_id = "kaeya"
    name = "ガイア"
    element = Element.CRYO
    weapon_type = "sword"
    max_hp = 10
    max_energy = 2
    normal_attack_cost = {DiceType.CRYO: 1, DiceType.ANY: 2}
    elemental_skill_cost = {DiceType.CRYO: 3}
    elemental_burst_cost = {DiceType.CRYO: 4}

    def create_state(self):
        state = super().create_state()
        state.add_status(StatusInstance(KaeyaActionTrigger))
        return state

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 3, Element.CRYO)

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 1, Element.CRYO)


KAEYA = Kaeya()
