from engine.events import RoundEndEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance, StatusRegistry
from engine.summons import SummonDefinition, SummonInstance, SummonRegistry


class CatalyzingField(StatusDefinition):
    status_id = "catalyzing_field"
    name = "激化フィールド"
    max_usages = 2


class DendroCore(StatusDefinition):
    status_id = "dendro_core"
    name = "草原核"
    max_usages = 2


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


DEFAULT_STATUS_REGISTRY = StatusRegistry((CatalyzingField, DendroCore))
DEFAULT_SUMMON_REGISTRY = SummonRegistry((BurningFlame,))


def create_catalyzing_field(usages: int = 2) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("catalyzing_field", usages=usages)


def create_dendro_core(usages: int = 1) -> StatusInstance:
    return DEFAULT_STATUS_REGISTRY.create("dendro_core", usages=usages)


def create_burning_flame(usages: int = 1) -> SummonInstance:
    return DEFAULT_SUMMON_REGISTRY.create("burning_flame", usages=usages)
