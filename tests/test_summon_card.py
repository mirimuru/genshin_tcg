from engine.cards import CardDefinition
from engine.events import RoundEndEvent
from engine.game import Game
from engine.state import GameState
from engine.statuses import StatusInstance
from engine.summons import SummonDefinition


class TestSummon(SummonDefinition):
    summon_id = "test_summon_card"
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
        game.state.players[player_id].add_summon(StatusInstance(TestSummon))


def test_card_can_generate_summon():
    game = Game(GameState.create_default())
    game.state.players[0].hand.append(TestSummonCard.card_id)
    game.card_registry.register(TestSummonCard)

    game._execute_card(type("Action", (), {"player_id": 0, "card_id": TestSummonCard.card_id, "target": None})())

    assert len(game.state.players[0].summons) == 1
    assert game.state.players[0].summons[0].definition is TestSummon


def test_summon_reacts_to_round_end():
    game = Game(GameState.create_default())
    game.state.players[0].add_summon(StatusInstance(TestSummon))
    hp_before = game.state.players[1].active_character.hp

    game._emit_event(RoundEndEvent(0))

    assert game.state.players[1].active_character.hp == hp_before - 1
    assert game.state.players[0].summons == []
