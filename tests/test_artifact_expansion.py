from content.cards.artifacts import INSTRUCTORS_CAP
from engine.dice import DiceType


def test_instructors_cap_has_artifact_slot_and_cost():
    assert INSTRUCTORS_CAP.equipment_slot == "artifact"
    assert INSTRUCTORS_CAP.cost == {DiceType.ANY: 2}


def test_artifact_registry_entry_is_exported():
    from content.cards import artifacts

    assert artifacts.INSTRUCTORS_CAP.card_id == "instructors_cap"


def test_artifact_can_be_equipped_without_replacing_weapon_or_talent():
    from content.characters import Diluc
    from content.cards.talents import COLD_BLOODED_STRIKE
    from content.cards.weapons import WOLF_GRAVESTONE
    from engine.state import CharacterState

    character = CharacterState(Diluc)
    character.add_equipment(WOLF_GRAVESTONE.create_status())
    character.add_equipment(COLD_BLOODED_STRIKE.create_status())
    character.add_equipment(INSTRUCTORS_CAP.create_status())

    slots = {status.definition.equipment_slot for status in character.statuses}
    assert slots == {"weapon", "talent", "artifact"}


def test_second_artifact_replaces_first_artifact_only():
    from content.characters import Diluc
    from engine.cards import ArtifactCardDefinition
    from engine.state import CharacterState
    from engine.statuses import ArtifactEquipmentStatusDefinition, StatusInstance

    class OtherArtifactStatus(ArtifactEquipmentStatusDefinition):
        status_id = "other_artifact"
        name = "Other Artifact"

    class OtherArtifact(ArtifactCardDefinition):
        card_id = "other_artifact"
        name = "Other Artifact"
        cost = {DiceType.ANY: 2}

        def create_status(self):
            return StatusInstance(OtherArtifactStatus)

    character = CharacterState(Diluc)
    character.add_equipment(INSTRUCTORS_CAP.create_status())
    character.add_equipment(OtherArtifact().create_status())

    assert len(character.statuses) == 1
    assert character.statuses[0].definition.status_id == "other_artifact"
