import pytest

from engine.characters import CharacterDefinition
from engine.dice import DiceType
from engine.state import Element, GameState, PlayerState
from engine.statuses import StatusDefinition, StatusInstance
from engine.summons import SummonDefinition, SummonInstance
from engine.evaluation import evaluate_state


class TestStatus(StatusDefinition):
    status_id = "test_status"
    name = "Test Status"
    max_usages = 2


class TestSummon(SummonDefinition):
    summon_id = "test_summon"
    name = "Test Summon"
    max_usages = 2


def make_game():
    def make_player(player_id):
        characters = [
            CharacterDefinition(f"c{player_id}_{i}", f"C{player_id}_{i}", Element.PYRO).create_state()
            for i in range(3)
        ]
        return PlayerState(player_id, characters)

    return GameState([make_player(0), make_player(1)])


def test_evaluation_is_zero_for_equal_initial_state():
    game = make_game()
    assert evaluate_state(game, 0) == pytest.approx(0.0)
    assert evaluate_state(game, 1) == pytest.approx(0.0)


def test_higher_own_hp_improves_evaluation_and_lower_enemy_hp_improves_it():
    game = make_game()
    base = evaluate_state(game, 0)

    game.players[0].active_character.receive_damage(3)
    assert evaluate_state(game, 0) < base

    game = make_game()
    game.players[1].active_character.receive_damage(3)
    assert evaluate_state(game, 0) > base


def test_more_alive_characters_improves_evaluation():
    game = make_game()
    base = evaluate_state(game, 0)
    game.players[1].characters[1].receive_damage(10)
    assert evaluate_state(game, 0) > base


def test_energy_dice_and_hand_are_evaluated():
    game = make_game()
    base = evaluate_state(game, 0)
    game.players[0].active_character.energy = 2
    game.players[0].dice.add(DiceType.PYRO, 2)
    game.players[0].hand.extend(["card-a", "card-b"])
    assert evaluate_state(game, 0) > base


def test_status_and_summon_are_evaluated():
    game = make_game()
    base = evaluate_state(game, 0)
    game.players[0].active_character.add_status(StatusInstance(TestStatus, usages=2))
    game.players[0].add_summon(SummonInstance(TestSummon, usages=2))
    assert evaluate_state(game, 0) > base


def test_aura_is_evaluated():
    game = make_game()
    base = evaluate_state(game, 0)
    game.players[0].active_character.elemental_aura = Element.PYRO
    assert evaluate_state(game, 0) != base


def test_terminal_state_dominates_normal_heuristics():
    game = make_game()
    game.players[1].characters[0].receive_damage(10)
    game.players[1].characters[1].receive_damage(10)
    game.players[1].characters[2].receive_damage(10)
    assert evaluate_state(game, 0) > 1000
    assert evaluate_state(game, 1) < -1000


def test_evaluation_is_from_player_perspective():
    game = make_game()
    game.players[0].active_character.receive_damage(2)
    game.players[1].active_character.receive_damage(4)
    assert evaluate_state(game, 0) == pytest.approx(-evaluate_state(game, 1))


def test_evaluation_does_not_mutate_state():
    game = make_game()
    game.players[0].active_character.energy = 1
    game.players[0].active_character.elemental_aura = Element.PYRO
    game.players[0].hand.append("card-a")
    before = game.copy()
    evaluate_state(game, 0)
    assert game.players[0].active_character.hp == before.players[0].active_character.hp
    assert game.players[0].active_character.energy == before.players[0].active_character.energy
    assert game.players[0].active_character.elemental_aura == before.players[0].active_character.elemental_aura
    assert game.players[0].hand == before.players[0].hand


def test_evaluation_rejects_invalid_player_id():
    with pytest.raises(ValueError):
        evaluate_state(make_game(), 2)
