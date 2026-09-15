import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


class RecordingDefinition:
    def __init__(self):
        self.calls = []

    def normal_attack(self, game, player_id):
        self.calls.append(("normal_attack", player_id))

    def elemental_skill(self, game, player_id):
        self.calls.append(("elemental_skill", player_id))

    def elemental_burst(self, game, player_id):
        self.calls.append(("elemental_burst", player_id))


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]
        for character in characters:
            character.definition = RecordingDefinition()
        players.append(PlayerState(player_id, characters))

    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_execute_action_dispatches_normal_attack():
    game = make_game()

    game.execute_action(Action(0, ActionType.NORMAL_ATTACK))

    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("normal_attack", 0)]
    assert game.state.current_player == 1


def test_execute_action_dispatches_elemental_skill():
    game = make_game()

    game.execute_action(Action(0, ActionType.ELEMENTAL_SKILL))

    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("elemental_skill", 0)]
    assert game.state.current_player == 1


def test_execute_action_dispatches_elemental_burst():
    game = make_game()
    game.state.players[0].active_character.energy = 2

    game.execute_action(Action(0, ActionType.ELEMENTAL_BURST))

    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("elemental_burst", 0)]
    assert game.state.current_player == 1


def test_execute_action_switches_character():
    game = make_game()

    game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=1))

    assert game.state.players[0].active_character_index == 1
    assert game.state.current_player == 1


def test_execute_action_rejects_invalid_switch_target():
    game = make_game()

    with pytest.raises(ValueError, match="交代"):
        game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=0))


def test_execute_action_requires_current_player():
    game = make_game()

    with pytest.raises(ValueError, match="現在のプレイヤー"):
        game.execute_action(Action(1, ActionType.NORMAL_ATTACK))


def test_execute_action_requires_forced_switch():
    game = make_game()
    game.state.players[0].active_character.receive_damage(999)

    with pytest.raises(ValueError, match="強制交代"):
        game.execute_action(Action(0, ActionType.NORMAL_ATTACK))


def test_execute_action_forced_switch_is_allowed():
    game = make_game()
    game.state.players[0].active_character.receive_damage(999)

    game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=1))

    assert game.state.players[0].active_character_index == 1


def test_end_round_passes_turn_to_opponent():
    game = make_game()

    game.execute_action(Action(0, ActionType.END_ROUND))

    assert game.state.players[0].has_ended_round
    assert game.state.current_player == 1
    assert game.state.round_number == 1


def test_end_round_starts_next_round_when_both_players_ended():
    game = make_game()

    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))

    assert game.state.round_number == 2
    assert game.state.current_player == 0
    assert game.state.phase.value == "roll"
    assert not game.state.players[0].has_ended_round
    assert not game.state.players[1].has_ended_round


def test_execute_action_rejects_actions_after_game_over():
    game = make_game()
    for character in game.state.players[1].characters:
        character.receive_damage(999)
    game.state.check_game_over()

    with pytest.raises(ValueError, match="ゲーム終了"):
        game.execute_action(Action(0, ActionType.END_ROUND))


def test_play_card_is_not_implemented_yet():
    game = make_game()

    with pytest.raises(NotImplementedError, match="カード"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_card"))
