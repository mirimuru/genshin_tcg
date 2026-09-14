from engine.state import CharacterState, Element


def test_damage_reduces_hp():
    character = CharacterState(
        name="テストキャラクター",
        element=Element.PYRO,
        max_hp=10,
    )

    character.receive_damage(3)

    assert character.hp == 7


def test_damage_cannot_reduce_hp_below_zero():
    character = CharacterState(
        name="テストキャラクター",
        element=Element.PYRO,
        max_hp=10,
    )

    character.receive_damage(100)

    assert character.hp == 0
    assert not character.alive