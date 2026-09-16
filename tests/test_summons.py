import pytest

from engine.state import CharacterState, Element, PlayerState
from engine.summons import SummonDefinition, SummonInstance, SummonRegistry


class TestSummon(SummonDefinition):
    summon_id = "test_summon"
    name = "テスト召喚"
    max_usages = 2


class UnlimitedSummon(SummonDefinition):
    summon_id = "unlimited_summon"
    name = "無期限召喚"
    max_usages = None


def test_summon_instance_uses_definition_and_consumes_usages():
    summon = SummonInstance(TestSummon)
    assert summon.summon_id == "test_summon"
    assert summon.name == "テスト召喚"
    assert summon.usages == 2
    assert summon.consume() == 1
    assert summon.usages == 1
    assert not summon.expired
    assert summon.consume(2) == 1
    assert summon.usages == 0
    assert summon.expired


def test_unlimited_summon_does_not_consume_usages():
    summon = SummonInstance(UnlimitedSummon)
    assert summon.usages is None
    assert summon.consume(3) == 0
    assert summon.usages is None
    assert not summon.expired


def test_summon_registry_resolves_and_creates_independent_instances():
    registry = SummonRegistry([TestSummon])
    first = registry.create("test_summon")
    second = registry.create("test_summon")
    first.consume()
    assert registry.get("test_summon").name == "テスト召喚"
    assert first.usages == 1
    assert second.usages == 2


def test_summon_registry_rejects_duplicate_and_unknown_ids():
    registry = SummonRegistry([TestSummon])
    with pytest.raises(ValueError, match="重複"):
        registry.register(TestSummon)
    with pytest.raises(ValueError, match="未登録"):
        registry.get("unknown_summon")


def test_summon_definition_and_instance_validate_types_and_usage_limits():
    with pytest.raises(TypeError):
        SummonInstance(object())
    with pytest.raises(ValueError):
        SummonInstance(TestSummon, usages=3)
    with pytest.raises(ValueError):
        SummonInstance(TestSummon, usages=-1)


def test_player_state_stores_summon_instances_and_replaces_same_id():
    player = PlayerState(0, [
        CharacterState("A", Element.PYRO),
        CharacterState("B", Element.HYDRO),
        CharacterState("C", Element.GEO),
    ])
    first = SummonInstance(TestSummon)
    second = SummonInstance(TestSummon)
    player.add_summon(first)
    first.consume()
    player.add_summon(second)
    assert player.get_summon("test_summon") is second
    assert second.usages == 2
    assert player.has_summon("test_summon")
    assert player.remove_summon("test_summon") is second
    assert not player.has_summon("test_summon")
