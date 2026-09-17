from engine.cards import CardDefinition
from engine.events import RoundEndEvent
from engine.summons import SummonDefinition, SummonInstance


class TestRoundEndSummon(SummonDefinition):
    summon_id = "test_round_end_summon"
    name = "テスト召喚"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            game.deal_damage(context.owner_id, 1, "pyro")
            instance.consume()


class TestSummonCard(CardDefinition):
    card_id = "test_summon_card"
    name = "テスト召喚カード"
    cost = {}

    def play(self, game, player_id, target=None):
        game.state.players[player_id].add_summon(SummonInstance(TestRoundEndSummon))


TEST_SUMMON_CARD = TestSummonCard
