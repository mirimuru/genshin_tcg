import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.simulation import simulate_round_roll
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from players.cpu import CpuPlayer


class RecordingDefinition:
    def normal_attack(self, game, player_id):
        pass

    def elemental_skill(self, game, player_id):
        pass

    def elemental_burst(self, game, player_id):
        pass


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState(f"キャラクター{index}", Element.PYRO)
            for index in range(3)
        ]
        for character in characters:
            character.definition = RecordingDefinition()
        players.append(PlayerState(player_id, characters))
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    return game


def test_simulate_round_roll_expands_both_players_independently(monkeypatch):
    game = make_game()

    outcomes = simulate_round_roll(game, count=1)

    assert len(outcomes) == 64
    assert sum(outcome.probability for outcome in outcomes) == pytest.approx(1.0)

    first = outcomes[0].state
    assert first is not game
    assert first.state.players[0].dice.total == 1
    assert first.state.players[1].dice.total == 1
    assert game.state.players[0].dice.total == 0
    assert game.state.players[1].dice.total == 0


def test_simulate_round_roll_probability_is_product_of_player_rolls():
    game = make_game()

    outcomes = simulate_round_roll(game, count=1)

    assert all(outcome.probability == pytest.approx(1 / 64) for outcome in outcomes)


def test_cpu_search_uses_chance_node_after_end_round():
    game = make_game()
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()

    cpu = CpuPlayer(search_depth=2, max_search_nodes=10_000)

    end_round = Action(0, ActionType.END_ROUND)
    value = cpu._evaluate_action(game, 0, end_round, depth=2)

    assert isinstance(value, float)
    assert cpu.last_search_nodes > 0
