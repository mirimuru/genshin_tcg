from content.cards.artifacts import INSTRUCTORS_CAP
from engine.dice import DiceType


def test_instructors_cap_has_artifact_slot_and_cost():
    assert INSTRUCTORS_CAP.equipment_slot == "artifact"
    assert INSTRUCTORS_CAP.cost == {DiceType.ANY: 2}


def test_instructors_cap_is_exported_from_content_cards():
    from content.cards import INSTRUCTORS_CAP as exported

    assert exported is INSTRUCTORS_CAP


def test_artifact_can_be_equipped_without_replacing_weapon_or_talent():
    from content.characters.kaeya import KAEYA
    from content.cards.talents import COLD_BLOODED_STRIKE
    from content.cards.weapons import TRAVELER_HANDY_SWORD

    character = KAEYA.create_state()
    character.add_equipment(TRAVELER_HANDY_SWORD.create_status())
    character.add_equipment(COLD_BLOODED_STRIKE.create_status())
    character.add_equipment(INSTRUCTORS_CAP.create_status())

    slots = {status.definition.equipment_slot for status in character.statuses}
    assert slots == {"weapon", "talent", "artifact"}


def test_second_artifact_replaces_first_artifact_only():
    from content.characters.diluc import DILUC
    from engine.cards import ArtifactCardDefinition
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

    character = DILUC.create_state()
    character.add_equipment(INSTRUCTORS_CAP.create_status())
    character.add_equipment(OtherArtifact().create_status())

    assert len(character.statuses) == 1
    assert character.statuses[0].definition.status_id == "other_artifact"
