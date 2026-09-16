from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from content.characters.diluc import DILUC


def make_game():
    players = [
        PlayerState(0, [DILUC.create_state(), CharacterState("控え1", Element.HYDRO), CharacterState("控え2", Element.CRYO)]),
        PlayerState(1, [CharacterState("敵", Element.HYDRO), CharacterState("敵2", Element.CRYO), CharacterState("敵3", Element.GEO)]),
    ]
    game = Game(GameState(players))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_diluc_has_real_tcg_costs_and_energy():
    game = make_game()
    character = game.state.players[0].active_character

    assert character.max_energy == 3
    assert game.get_action_cost(type("A", (), {"action_type": __import__("engine.actions", fromlist=["ActionType"]).ActionType.NORMAL_ATTACK, "player_id": 0})()) == {
        __import__("engine.dice", fromlist=["DiceType"]).DiceType.PYRO: 1,
        __import__("engine.dice", fromlist=["DiceType"]).DiceType.ANY: 2,
    }


def test_diluc_third_skill_in_round_deals_two_extra_damage():
    game = make_game()
    target = game.state.players[1].active_character

    game.elemental_skill(0)
    target.hp = 10
    target.elemental_aura = None
    game.elemental_skill(0)
    target.hp = 10
    target.elemental_aura = None
    game.elemental_skill(0)

    assert target.hp == 5


def test_diluc_skill_counter_resets_at_round_end():
    game = make_game()
    target = game.state.players[1].active_character

    game.elemental_skill(0)
    target.hp = 10
    target.elemental_aura = None
    game._resolve_end_of_round_effects()
    game.elemental_skill(0)

    assert target.hp == 7


def test_diluc_burst_deals_eight_and_applies_pyro_infusion():
    game = make_game()
    character = game.state.players[0].active_character
    target = game.state.players[1].active_character
    character.energy = 3

    game.elemental_burst(0)

    assert target.hp == 2
    assert character.energy == 0
    assert character.has_status("pyro_infusion")


def test_diluc_pyro_infusion_converts_normal_attack_to_pyro():
    game = make_game()
    character = game.state.players[0].active_character
    target = game.state.players[1].active_character
    character.energy = 3
    game.elemental_burst(0)
    target.hp = 10
    target.elemental_aura = Element.HYDRO

    game.normal_attack(0)

    assert target.hp == 5
    assert target.elemental_aura is None


def test_diluc_pyro_infusion_expires_after_two_rounds():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = 3
    game.elemental_burst(0)

    assert character.has_status("pyro_infusion")
    game._resolve_end_of_round_effects()
    assert character.has_status("pyro_infusion")
    game._resolve_end_of_round_effects()
    assert not character.has_status("pyro_infusion")
