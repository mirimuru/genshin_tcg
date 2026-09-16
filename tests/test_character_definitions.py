from content.characters.diluc import DILUC
from engine.characters import CharacterRegistry
from engine.state import Element


def test_diluc_definition_has_character_metadata():
    assert DILUC.character_id == "diluc"
    assert DILUC.name == "ディルック"
    assert DILUC.element is Element.PYRO
    assert DILUC.max_hp == 10
    assert DILUC.max_energy == 2


def test_diluc_definition_creates_character_state():
    state = DILUC.create_state()
    assert state.definition is DILUC
    assert state.name == "ディルック"
    assert state.element is Element.PYRO
    assert state.hp == 10
    assert state.energy == 0


def test_character_registry_resolves_diluc():
    registry = CharacterRegistry([DILUC])
    assert registry.get("diluc") is DILUC
    assert registry.contains("diluc")
