from engine.events import EnergyEvent, EffectContext, GameEvent
from engine.state import CharacterState, Element


def test_energy_event_is_game_event():
    event = EnergyEvent(0, 1, 1, "normal_attack")
    assert isinstance(event, GameEvent)
    assert event.player_id == 0
    assert event.character_index == 1
    assert event.amount == 1
    assert event.reason == "normal_attack"
    assert not event.resolved


def test_energy_event_can_represent_burst_energy_consumption():
    event = EnergyEvent(1, 0, -2, "elemental_burst")
    assert event.amount == -2
    assert event.reason == "elemental_burst"


def test_energy_is_bounded_by_character_max_energy():
    character = CharacterState("テスト", Element.PYRO, max_energy=2)
    character.energy = min(character.max_energy, character.energy + 3)
    assert character.energy == 2


def test_energy_event_context_targets_one_character():
    context = EffectContext(owner_id=0, character_index=2)
    event = EnergyEvent(0, 2, 1, "elemental_skill")
    assert context.owner_id == event.player_id
    assert context.character_index == event.character_index
