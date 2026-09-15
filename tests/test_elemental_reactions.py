from engine.elemental_reactions import ElementalReaction, ReactionResolver
from engine.state import Element


def test_pyro_hydro_causes_vaporize():
    result = ReactionResolver.resolve(Element.PYRO, Element.HYDRO)

    assert result.reaction is ElementalReaction.VAPORIZE


def test_hydro_pyro_causes_vaporize_regardless_of_order():
    result = ReactionResolver.resolve(Element.HYDRO, Element.PYRO)

    assert result.reaction is ElementalReaction.VAPORIZE


def test_pyro_cryo_causes_melt():
    result = ReactionResolver.resolve(Element.PYRO, Element.CRYO)

    assert result.reaction is ElementalReaction.MELT


def test_hydro_electro_causes_electro_charged():
    result = ReactionResolver.resolve(Element.HYDRO, Element.ELECTRO)

    assert result.reaction is ElementalReaction.ELECTRO_CHARGED


def test_hydro_cryo_causes_frozen():
    result = ReactionResolver.resolve(Element.HYDRO, Element.CRYO)

    assert result.reaction is ElementalReaction.FROZEN


def test_electro_cryo_causes_superconduct():
    result = ReactionResolver.resolve(Element.ELECTRO, Element.CRYO)

    assert result.reaction is ElementalReaction.SUPERCONDUCT


def test_cryo_electro_causes_superconduct_regardless_of_order():
    result = ReactionResolver.resolve(Element.CRYO, Element.ELECTRO)

    assert result.reaction is ElementalReaction.SUPERCONDUCT


def test_electro_dendro_causes_quicken():
    result = ReactionResolver.resolve(Element.ELECTRO, Element.DENDRO)

    assert result.reaction is ElementalReaction.QUICKEN


def test_pyro_dendro_causes_burning():
    result = ReactionResolver.resolve(Element.PYRO, Element.DENDRO)

    assert result.reaction is ElementalReaction.BURNING


def test_anemo_pyro_causes_swirl():
    result = ReactionResolver.resolve(Element.ANEMO, Element.PYRO)

    assert result.reaction is ElementalReaction.SWIRL


def test_anemo_dendro_does_not_swirl():
    result = ReactionResolver.resolve(Element.ANEMO, Element.DENDRO)

    assert result.reaction is None


def test_geo_pyro_causes_crystallize():
    result = ReactionResolver.resolve(Element.GEO, Element.PYRO)

    assert result.reaction is ElementalReaction.CRYSTALLIZE


def test_same_element_does_not_react():
    result = ReactionResolver.resolve(Element.PYRO, Element.PYRO)

    assert result.reaction is None


def test_unreactive_pair_does_not_react():
    result = ReactionResolver.resolve(Element.DENDRO, Element.CRYO)

    assert result.reaction is None


def test_anemo_physical_does_not_react():
    result = ReactionResolver.resolve(Element.ANEMO, Element.PHYSICAL)

    assert result.reaction is None


def test_geo_dendro_does_not_react():
    result = ReactionResolver.resolve(Element.GEO, Element.DENDRO)

    assert result.reaction is None
