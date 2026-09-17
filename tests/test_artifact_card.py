import pytest

from engine.cards import CardRegistry
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from engine.statuses import EquipmentStatusDefinition, StatusInstance
from content.cards.artifacts import INSTRUCTORS_CAP, InstructorsCapStatus


def make_game():
    players = [
        PlayerState(0, [
            CharacterState("A", Element.PYRO),
            CharacterState("B", Element.HYDRO),
            CharacterState("C", Element.CRYO),
        ]),
        PlayerState(1, [
            CharacterState("X", Element.HYDRO, max_hp=100),
            CharacterState("Y", Element.PYRO),
            CharacterState("Z", Element.CRYO),
        ]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 8})
    players[1].dice = DicePool({DiceType.OMNI: 8})
    return game


def test_artifact_equipment_status_uses_artifact_slot():
    status = StatusInstance(InstructorsCapStatus)

    assert isinstance(status.definition, EquipmentStatusDefinition)
    assert status.definition.equipment_slot == "artifact"


def test_artifact_card_equips_to_active_character():
    game = make_game()
    player = game.state.players[0]
    player.dice = DicePool({DiceType.OMNI: 2})
    game.card_registry = CardRegistry([INSTRUCTORS_CAP])
    player.hand = ["instructors_cap"]

    game.execute_action(__import__("engine.actions", fromlist=["Action"]).Action(
        0, __import__("engine.actions", fromlist=["ActionType"]).ActionType.PLAY_CARD, card_id="instructors_cap"
    ))

    assert player.active_character.has_status("instructors_cap")
    assert player.dice.total == 0


def test_artifact_replaces_only_existing_artifact_slot():
    game = make_game()
    character = game.state.players[0].active_character
    character.add_equipment(StatusInstance(InstructorsCapStatus))

    class OtherArtifact(EquipmentStatusDefinition):
        status_id = "other_artifact"
        name = "別の聖遺物"
        equipment_slot = "artifact"

    character.add_equipment(StatusInstance(OtherArtifact))

    assert character.has_status("other_artifact")
    assert not character.has_status("instructors_cap")


def test_artifact_does_not_replace_weapon_or_talent_slots():
    game = make_game()
    character = game.state.players[0].active_character

    from content.cards.weapons import TravelerHandySwordStatus
    from content.cards.talents import ColdBloodedStrikeStatus

    character.add_equipment(StatusInstance(TravelerHandySwordStatus))
    character.add_equipment(StatusInstance(ColdBloodedStrikeStatus))
    character.add_equipment(StatusInstance(InstructorsCapStatus))

    assert character.has_status("traveler_handy_sword")
    assert character.has_status("cold_blooded_strike")
    assert character.has_status("instructors_cap")


def test_instructors_cap_generates_matching_elemental_die_after_equipped_character_triggers_reaction():
    game = make_game()
    character = game.state.players[0].active_character
    character.add_equipment(StatusInstance(InstructorsCapStatus))
    game.state.players[1].active_character.elemental_aura = Element.HYDRO

    before = game.state.players[0].dice.total
    game.deal_damage(0, 1, 2, Element.PYRO)

    assert game.state.players[0].dice.total == before + 1
    assert game.state.players[0].dice.count(DiceType.PYRO) == 1


def test_instructors_cap_triggers_at_most_three_times_per_round_and_resets_next_round():
    game = make_game()
    character = game.state.players[0].active_character
    character.add_equipment(StatusInstance(InstructorsCapStatus))

    for _ in range(4):
        game.state.players[1].active_character.elemental_aura = Element.HYDRO
        game.deal_damage(0, 1, 1, Element.PYRO)

    assert game.state.players[0].dice.count(DiceType.PYRO) == 3

    from engine.events import RoundEndEvent
    game._emit_event(RoundEndEvent(0))
    game.state.players[1].active_character.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 1, Element.PYRO)

    assert game.state.players[0].dice.count(DiceType.PYRO) == 4


def test_instructors_cap_does_not_trigger_for_reaction_caused_by_another_character():
    game = make_game()
    character = game.state.players[0].characters[1]
    character.add_equipment(StatusInstance(InstructorsCapStatus))
    game.state.players[0].active_character_index = 0
    game.state.players[1].active_character.elemental_aura = Element.HYDRO

    before = game.state.players[0].dice.total
    game.deal_damage(0, 1, 1, Element.PYRO)

    assert game.state.players[0].dice.total == before
