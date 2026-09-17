"""Additional artifact-card implementations."""

from engine.cards import ArtifactCardDefinition
from engine.dice import DiceType
from engine.statuses import ArtifactEquipmentStatusDefinition, StatusInstance


class SimpleArtifactStatus(ArtifactEquipmentStatusDefinition):
    """Minimal reference artifact status used to verify artifact extensibility."""

    status_id = "simple_artifact"
    name = "Simple Artifact"


class SimpleArtifact(ArtifactCardDefinition):
    """Minimal reference artifact card for the artifact framework."""

    card_id = "simple_artifact"
    name = "Simple Artifact"
    cost = {DiceType.ANY: 2}

    def create_status(self):
        return StatusInstance(SimpleArtifactStatus)


SIMPLE_ARTIFACT = SimpleArtifact()

__all__ = ["SimpleArtifact", "SIMPLE_ARTIFACT", "SimpleArtifactStatus"]
