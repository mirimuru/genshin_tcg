from engine.elemental_reactions import ElementalReaction
from engine.events import DamageEvent, RoundEndEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance, StatusRegistry
from engine.summons import SummonDefinition, SummonInstance, SummonRegistry


class CatalyzingField(StatusDefinition):
    status_id = "catalyzing_field"
    name = "激化フィールド"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if not isinstance(event, DamageEvent) or event.resolved or event.attacker_id != context.owner_id:
            return
        if event.element not in {Element.DENDRO, Element.ELECTRO}:
            return
        if not instance.usages:
            return
        instance.consume()
        if event.reaction is not ElementalReaction.QUICKEN:
            event.amount += 1


class DendroCore(StatusDefinition):
    status_id = "dendro_core"
    name = "草原核"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if not isinstance(event, DamageEvent) or event.resolved or event.attacker_id != context.owner_id:
            return
        if event.element not in {Element.PYRO, Element.ELECTRO}:
            return
        if not instance.usages:
            return
        instance.consume()
        event.amount += 2


class BloomCoreGeneration(StatusDefinition):
    status_id = "bloom_core_generation"
    name = "草原核生成"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if not isinstance(event, DamageEvent) or event.resolved:
            return
        if event.attacker_id != context.owner_id or event.reaction is not ElementalReaction.BLOOM:
            return
        player = game.state.players[context.owner_id]
        existing = player.get_combat_status("dendro_core")
        if existing is None:
            player.add_combat_status(create_dendro_core(1))
        else:
            existing.usages = min(2, (existing.usages or 0) + 1)
        instance.consume()


class CrystallizeShield(StatusDefinition):
    status_id = "crystallize_shield"
    name = "結晶シールド生成"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if not isinstance(event, DamageEvent) or not event.resolved:
            return
        if event.target_id != context.owner_id or event.reaction is not ElementalReaction.CRYSTALLIZE:
            return
        if game.state.players[context.owner_id].active_character.alive:
            game.state.players[context.owner_id].add_shield(1)
        instance.consume()


class BurningFlameGeneration(StatusDefinition):
    status_id = "burning_flame_generation"
    name = "燃焼の炎生成"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if not isinstance(event, DamageEvent) or event.resolved:
            return
        if event.attacker_id != context.owner_id or event.reaction is not ElementalReaction.BURNING:
            return
        player = game.state.players[context.owner_id]
        existing = player.get_summon("burning_flame")
        if existing is None:
            player.add_summon(create_burning_flame(1))
        else:
            existing.usages = min(2, (existing.usages or 0) + 1)
        instance.consume()


class BurningFlame(SummonDefinition):
    summon_id = "burning_flame"
    name = "燃焼の炎"
    max_usages = 2

    def on_event(self, instance, event, game, context):
        if not isinstance(event, RoundEndEvent) or event.player_id != context.owner_id:
            return
        uses = instance.usages or 0
        instance.usages = 0
        for _ in range(uses):
            if game.state.game_over:
                break
            game.deal_damage(context.owner_id, 1 - context.owner_id, 1, Element.PYRO)


DEFAULT_STATUS_REGISTRY = StatusRegistry((CatalyzingField, DendroCore, BloomCoreGeneration, CrystallizeShield, BurningFlameGeneration))
DEFAULT_SUMMON_REGISTRY = SummonRegistry((BurningFlame,))


def create_catalyzing_field(usages: int = 2) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("catalyzing_field", usages=usages)


def create_dendro_core(usages: int = 1) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("dendro_core", usages=usages)


def create_bloom_core_generation(usages: int = 1) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("bloom_core_generation", usages=usages)


def create_crystallize_shield(usages: int = 1) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("crystallize_shield", usages=usages)


def create_burning_flame_generation(usages: int = 1) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("burning_flame_generation", usages=usages)


def create_burning_flame(usages: int = 1) -> SummonInstance:
    return DEFAULT_SUMMON_REGISTRY.create("burning_flame", usages=usages)
