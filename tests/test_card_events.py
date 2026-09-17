import pytest

from engine.actions import Action, ActionType
from engine.cards import CardDefinition, CardRegistry
from engine.dice import DicePool, DiceType
from engine.events import CardActionEvent
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from engine.statuses import StatusDefinition, StatusInstance


class EventProbe(StatusDefinition):
    status_id = "event_probe"
    name = "イベント検証"
    max_usages = None

    def on_event(self, instance, event, game, context):
        if isinstance(event, CardActionEvent):
            instance.data.setdefault("events", []).append(
                (event.player_id, event.card_id, event.target, event.resolved)
            )


class EventProbeCard(CardDefinition):
    card_id = "test_event_probe"
    name = "イベント検証カード"
    cost = {DiceType.ANY: 1}

    def play(self, game, player_id, target=None):
        character = game.state.players[player_id].active_character
        character.heal(1)


def make_game():
    players = [
        PlayerState(0, [
            CharacterState("A", Element.PYRO),
            CharacterState("B", Element.HYDRO),
            CharacterState("C", Element.CRYO),
        ]),
        PlayerState(1, [
            CharacterState("X", Element.PYRO),
            CharacterState("Y", Element.HYDRO),
            CharacterState("Z", Element.CRYO),
        ]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 3})
    players[1].dice = DicePool({DiceType.OMNI: 3})
    return game


def test_card_action_event_contains_card_data_and_defaults_to_unresolved():
    event = CardActionEvent(0, "test_event_probe", target=2)

    assert event.player_id == 0
    assert event.card_id == "test_event_probe"
    assert event.target == 2
    assert event.resolved is False


def test_play_card_emits_unresolved_and_resolved_events():
    game = make_game()
    game.card_registry = CardRegistry([EventProbeCard])
    player = game.state.players[0]
    player.hand = ["test_event_probe"]
    player.active_character.hp = 5
    player.active_character.add_status(StatusInstance(EventProbe))

    game.execute_action(
        Action(0, ActionType.PLAY_CARD, card_id="test_event_probe", target=2)
    )

    events = player.active_character.get_status("event_probe").data["events"]
    assert events == [
        (0, "test_event_probe", 2, False),
        (0, "test_event_probe", 2, True),
    ]
    assert player.active_character.hp == 6


def test_card_action_event_is_snapshot_notified():
    class AddProbe(StatusDefinition):
        status_id = "add_probe"
        name = "追加検証"
        max_usages = None

        def on_event(self, instance, event, game, context):
            if isinstance(event, CardActionEvent) and not event.resolved:
                game.state.players[context.owner_id].active_character.add_status(
                    StatusInstance(EventProbe)
                )

    game = make_game()
    game.card_registry = CardRegistry([EventProbeCard])
    player = game.state.players[0]
    player.hand = ["test_event_probe"]
    player.active_character.add_status(StatusInstance(AddProbe))

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_event_probe", target=None))

    probe = player.active_character.get_status("event_probe")
    assert probe is not None
    assert probe.data.get("events") == [(0, "test_event_probe", None, True)]
