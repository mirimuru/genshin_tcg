import pytest

from engine.state import CharacterState, Element, PlayerState
from engine.statuses import StatusDefinition, StatusInstance


class TestCharacterStatus(StatusDefinition):
    status_id = "test_character_status"
    name = "テストキャラクター状態"
    max_usages = 2


class TestCombatStatus(StatusDefinition):
    status_id = "test_combat_status"
    name = "テスト戦闘状態"
    max_usages = 3


def make_player():
    return PlayerState(
        0,
        [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ],
    )


def test_character_can_add_find_and_remove_status():
    character = CharacterState("キャラクター", Element.PYRO)
    status = StatusInstance(TestCharacterStatus)

    assert character.add_status(status) is status
    assert character.has_status("test_character_status")
    assert character.get_status("test_character_status") is status

    removed = character.remove_status("test_character_status")
    assert removed is status
    assert not character.has_status("test_character_status")
    assert character.get_status("test_character_status") is None


def test_character_replaces_existing_status_with_same_id():
    character = CharacterState("キャラクター", Element.PYRO)
    first = StatusInstance(TestCharacterStatus, usages=1)
    second = StatusInstance(TestCharacterStatus, usages=2)

    character.add_status(first)
    character.add_status(second)

    assert character.get_status("test_character_status") is second
    assert len(character.statuses) == 1


def test_character_status_can_be_consumed_and_removed_when_expired():
    character = CharacterState("キャラクター", Element.PYRO)
    character.add_status(StatusInstance(TestCharacterStatus))

    status = character.get_status("test_character_status")
    assert status is not None
    assert status.consume() == 1
    assert character.has_status("test_character_status")
    assert status.consume() == 1

    character.remove_expired_statuses()
    assert not character.has_status("test_character_status")


def test_player_can_manage_combat_statuses_independently_from_characters():
    player = make_player()
    status = StatusInstance(TestCombatStatus)

    assert player.add_combat_status(status) is status
    assert player.has_combat_status("test_combat_status")
    assert player.get_combat_status("test_combat_status") is status
    assert player.characters[0].get_status("test_combat_status") is None

    assert player.remove_combat_status("test_combat_status") is status
    assert not player.has_combat_status("test_combat_status")


def test_status_methods_reject_duplicate_and_invalid_status_objects():
    character = CharacterState("キャラクター", Element.PYRO)
    character.add_status(StatusInstance(TestCharacterStatus))

    with pytest.raises(TypeError):
        character.add_status(object())

    with pytest.raises(TypeError):
        character.add_status(StatusInstance(TestCharacterStatus)) if False else character.add_status("bad")
