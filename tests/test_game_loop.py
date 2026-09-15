import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
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
    return Game(GameState(players))


def test_step_executes_roll_phase_then_action_phase():
    game = make_game()
    players = [CpuPlayer(), CpuPlayer()]

    first = game.step(players)
    second = game.step(players)

    assert first.action_type is ActionType.REROLL_DICE
    assert second.action_type is ActionType.REROLL_DICE
    assert game.state.phase is GamePhase.ACTION
    assert game.state.current_player == 0

    game.state.players[0].dice = DicePool.default()
    action = game.step(players)

    assert action.player_id == 0
    assert action.action_type is ActionType.ELEMENTAL_SKILL
    assert game.state.current_player == 1


def test_run_stops_at_max_actions_after_round_transition():
    game = make_game()

    class EndRoundPlayer:
        def choose_action(self, game, player_id, legal_actions=None):
            return next(action for action in legal_actions if action.action_type is ActionType.END_ROUND)

    actions = game.run([EndRoundPlayer(), EndRoundPlayer()], max_actions=4)

    assert len(actions) == 4
    assert game.state.round_number == 2
    assert game.state.phase is GamePhase.ROLL
    assert game.state.current_player == 0


def test_step_rejects_game_without_legal_actions():
    game = make_game()
    game.state.game_over = True

    with pytest.raises(ValueError, match="合法手"):
        game.step([CpuPlayer(), CpuPlayer()])


def test_run_obeys_max_actions():
    game = make_game()
    actions = game.run([CpuPlayer(), CpuPlayer()], max_actions=3)

    assert len(actions) == 3
