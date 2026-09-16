from engine.effects import create_catalyzing_field, create_dendro_core
from engine.elemental_reactions import ElementalReaction
from engine.events import DamageEvent, RoundEndEvent
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from engine.statuses import StatusDefinition, StatusInstance
from engine.summons import SummonDefinition, SummonInstance


class DamageBonusStatus(StatusDefinition):
    status_id = "damage_bonus_status"
    name = "ダメージ加算テスト"
    max_usages = None

    def on_event(self, instance, event, game, context):
        if isinstance(event, DamageEvent) and event.attacker_id == context.owner_id:
            event.amount += 1


class RoundEndStatus(StatusDefinition):
    status_id = "round_end_status"
    name = "ラウンド終了テスト"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            instance.consume()


class RoundEndSummon(SummonDefinition):
    summon_id = "round_end_summon"
    name = "ラウンド終了召喚物テスト"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            instance.consume()


def make_game():
    players = []
    for player_id in (0, 1):
        players.append(PlayerState(player_id, [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]))
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    return game


def test_damage_event_is_dispatched_to_character_statuses():
    game = make_game()
    attacker = game.state.players[0].active_character
    attacker.add_status(StatusInstance(DamageBonusStatus))
    target = game.state.players[1].active_character

    game.deal_damage(0, 1, 1, Element.PYRO)

    assert target.hp == 8


def test_round_end_event_is_dispatched_to_combat_statuses_and_summons():
    game = make_game()
    player = game.state.players[0]
    player.add_combat_status(StatusInstance(RoundEndStatus))
    player.add_summon(SummonInstance(RoundEndSummon))

    game._emit_event(RoundEndEvent(player_id=0))

    assert player.get_combat_status("round_end_status") is None
    assert player.get_summon("round_end_summon") is None


def test_catalyzing_field_applies_non_quicken_dendro_or_electro_bonus_from_damage_event():
    game = make_game()
    attacker = game.state.players[0]
    attacker.add_combat_status(create_catalyzing_field(2))

    event = DamageEvent(0, 1, 1, Element.DENDRO, None)
    game._emit_event(event)

    assert event.amount == 2
    assert attacker.get_combat_status("catalyzing_field").usages == 1


def test_catalyzing_field_is_consumed_without_bonus_on_quicken_damage_event():
    game = make_game()
    attacker = game.state.players[0]
    attacker.add_combat_status(create_catalyzing_field(2))

    event = DamageEvent(0, 1, 1, Element.ELECTRO, ElementalReaction.QUICKEN)
    game._emit_event(event)

    assert event.amount == 1
    assert attacker.get_combat_status("catalyzing_field").usages == 1


def test_dendro_core_adds_two_damage_to_pyro_or_electro_damage_event():
    game = make_game()
    attacker = game.state.players[0]
    attacker.add_combat_status(create_dendro_core(1))

    event = DamageEvent(0, 1, 1, Element.PYRO, None)
    game._emit_event(event)

    assert event.amount == 3
    assert attacker.get_combat_status("dendro_core") is None


def test_event_types_are_independent_data_objects():
    damage = DamageEvent(0, 1, 2, Element.PYRO)
    round_end = RoundEndEvent(0)
    assert damage.amount == 2
    assert damage.reaction is None
    assert round_end.player_id == 0
