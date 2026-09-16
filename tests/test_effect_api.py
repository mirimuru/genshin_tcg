from dataclasses import dataclass

from engine.events import GameEvent
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from engine.statuses import StatusDefinition, StatusInstance
from engine.summons import SummonDefinition, SummonInstance


class TestCharacterStatus(StatusDefinition):
    status_id = "test_character_status"
    name = "テストCharacter Status"
    max_usages = 2


class TestCombatStatus(StatusDefinition):
    status_id = "test_combat_status"
    name = "テストCombat Status"
    max_usages = 2


class TestSummon(SummonDefinition):
    summon_id = "test_summon"
    name = "テスト召喚物"
    max_usages = 2


def make_game():
    players = [
        PlayerState(0, [CharacterState(f"P0-{i}", Element.PYRO) for i in range(3)]),
        PlayerState(1, [CharacterState(f"P1-{i}", Element.HYDRO) for i in range(3)]),
    ]
    return Game(GameState(players))


def test_add_character_status_to_specific_character():
    game = make_game()
    status = StatusInstance(TestCharacterStatus)

    result = game.add_character_status(0, 1, status)

    assert result is status
    assert game.state.players[0].characters[1].get_status("test_character_status") is status
    assert not game.state.players[0].characters[0].has_status("test_character_status")


def test_add_character_status_rejects_invalid_character_index():
    game = make_game()
    status = StatusInstance(TestCharacterStatus)

    try:
        game.add_character_status(0, 3, status)
    except ValueError as exc:
        assert "character_index" in str(exc)
    else:
        raise AssertionError("ValueErrorが発生していません")


def test_add_character_status_rejects_invalid_status_type():
    game = make_game()

    try:
        game.add_character_status(0, 0, object())
    except TypeError:
        pass
    else:
        raise AssertionError("TypeErrorが発生していません")


def test_add_combat_status():
    game = make_game()
    status = StatusInstance(TestCombatStatus)

    assert game.add_combat_status(0, status) is status
    assert game.state.players[0].get_combat_status("test_combat_status") is status


def test_add_summon():
    game = make_game()
    summon = SummonInstance(TestSummon)

    assert game.add_summon(1, summon) is summon
    assert game.state.players[1].get_summon("test_summon") is summon


@dataclass
class TestEvent(GameEvent):
    value: int


class EventStatus(StatusDefinition):
    status_id = "event_status"
    name = "イベントテスト"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, TestEvent):
            instance.consume()


def test_effect_added_through_api_receives_events_and_expires():
    game = make_game()
    status = StatusInstance(EventStatus)
    game.add_character_status(0, 0, status)

    game._emit_event(TestEvent(1))

    assert not game.state.players[0].characters[0].has_status("event_status")
