import pytest

from engine.statuses import StatusDefinition, StatusInstance, StatusRegistry


class TestStatus(StatusDefinition):
    status_id = "test_status"
    name = "テスト状態"
    max_usages = 3


def test_status_instance_starts_with_definition_max_usages():
    status = StatusInstance(TestStatus)

    assert status.status_id == "test_status"
    assert status.name == "テスト状態"
    assert status.usages == 3


def test_status_instance_consumes_usages_without_going_below_zero():
    status = StatusInstance(TestStatus, usages=2)

    assert status.consume() == 1
    assert status.usages == 1
    assert status.consume(5) == 1
    assert status.usages == 0
    assert status.consume() == 0


def test_status_instance_rejects_invalid_usage_values():
    with pytest.raises(ValueError):
        StatusInstance(TestStatus, usages=-1)

    with pytest.raises(ValueError):
        StatusInstance(TestStatus, usages=4)


def test_status_registry_registers_and_resolves_definitions():
    registry = StatusRegistry([TestStatus])

    status = registry.create("test_status")

    assert isinstance(status, StatusInstance)
    assert status.definition is not TestStatus
    assert status.status_id == "test_status"
    assert registry.get("test_status").status_id == "test_status"


def test_status_registry_rejects_unknown_or_duplicate_ids():
    registry = StatusRegistry([TestStatus])

    with pytest.raises(ValueError, match="未登録"):
        registry.get("unknown")

    with pytest.raises(ValueError, match="重複"):
        registry.register(TestStatus)
