from content.characters.xiangling import XIANG_LING
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [XIANG_LING.create_state(), CharacterState("控え1", Element.HYDRO), CharacterState("控え2", Element.CRYO)]),
        PlayerState(1, [CharacterState("相手1", Element.HYDRO), CharacterState("相手2", Element.ELECTRO), CharacterState("相手3", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    return game


def test_xiangling_has_official_stats_and_costs():
    state = XIANG_LING.create_state()
    assert state.max_hp == 10
    assert state.max_energy == 2
    assert XIANG_LING.normal_attack_cost
    assert XIANG_LING.elemental_skill_cost
    assert XIANG_LING.elemental_burst_cost


def test_xiangling_skill_creates_guoba_via_resolved_skill_event():
    game = make_game()
    game.elemental_skill(0)

    guoba = game.state.players[0].get_summon("guoba")
    assert guoba is not None
    assert guoba.usages == 2


def test_guoba_deals_two_pyro_at_round_end_and_consumes_one_usage():
    game = make_game()
    game.elemental_skill(0)
    target = game.state.players[1].active_character

    game._resolve_end_of_round_effects()

    assert target.hp == 8
    assert game.state.players[0].get_summon("guoba").usages == 1


def test_xiangling_burst_creates_pyronado():
    game = make_game()
    game.state.players[0].active_character.energy = 2

    game.elemental_burst(0)

    pyronado = game.state.players[0].get_summon("pyronado")
    assert pyronado is not None
    assert pyronado.usages == 2


def test_pyronado_triggers_after_a_later_skill():
    game = make_game()
    game.state.players[0].active_character.energy = 2
    game.elemental_burst(0)
    target = game.state.players[1].active_character

    game.elemental_skill(0)

    assert target.hp == 5
    assert game.state.players[0].get_summon("pyronado").usages == 1
