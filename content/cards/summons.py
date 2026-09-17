from engine.cards import CardDefinition
from engine.dice import DiceType
from engine.events import RoundEndEvent
from engine.state import Element
from engine.summons import SummonDefinition, SummonInstance


class _HilichurlSummon(SummonDefinition):
    """アビスの呼びかけで生成されるヒルチャール召喚物の共通実装。"""

    max_usages = 2
    damage = 1
    element = Element.PHYSICAL

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            game.deal_damage(context.owner_id, 1 - context.owner_id, self.damage, self.element)
            instance.consume()


class HilichurlCryo(_HilichurlSummon):
    summon_id = "hilichurl_cryo"
    name = "ヒルチャール・氷矢"
    element = Element.CRYO


class HilichurlHydro(_HilichurlSummon):
    summon_id = "hilichurl_hydro"
    name = "ヒルチャールシャーマン・水"
    element = Element.HYDRO


class HilichurlPyro(_HilichurlSummon):
    summon_id = "hilichurl_pyro"
    name = "ヒルチャール・突進"
    element = Element.PYRO


class HilichurlElectro(_HilichurlSummon):
    summon_id = "hilichurl_electro"
    name = "ヒルチャール・雷矢"
    element = Element.ELECTRO


class AbyssCall(CardDefinition):
    """アビスの呼びかけ。ランダムなヒルチャールを1体召喚する。"""

    card_id = "abyss_call"
    name = "アビスの呼びかけ"
    cost = {DiceType.ANY: 2}

    def play(self, game, player_id, target=None):
        summon_type = game.rng.choice(
            (HilichurlCryo, HilichurlHydro, HilichurlPyro, HilichurlElectro)
        )
        game.state.players[player_id].add_summon(SummonInstance(summon_type))


ABYSS_CALL = AbyssCall()

__all__ = [
    "AbyssCall",
    "ABYSS_CALL",
    "HilichurlCryo",
    "HilichurlHydro",
    "HilichurlPyro",
    "HilichurlElectro",
]
