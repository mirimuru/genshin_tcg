from types import SimpleNamespace

from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from players.cpu import CpuPlayer


def make_player(player_id):
    characters = [
        CharacterState("Character 1", Element.PYRO),
        CharacterState("Character 2", Element.HYDRO),
        CharacterState("Character 3", Element.CRYO),
    ]
    return PlayerState(player_id, characters)


def make_game():
    state = GameState([make_player(0), make_player(1)])
    game = Game(state)
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_cpu_uses_burst_when_energy_is_full():
    game = make_game()
    game.state.players[0].active_character.energy = 2

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.ELEMENTAL_BURST
    assert action.player_id == 0


def test_cpu_switches_when_active_character_is_defeated():
    game = make_game()

    game.state.players[0].active_character.receive_damage(999)

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.SWITCH_CHARACTER
    assert action.target == 1


def test_cpu_switches_from_low_hp_character():
    game = make_game()

    game.state.players[0].active_character.receive_damage(8)

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.SWITCH_CHARACTER
    assert action.target == 1


def test_cpu_uses_skill_when_no_higher_priority_action_exists():
    game = make_game()

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.ELEMENTAL_SKILL
    assert action.target is None


def test_cpu_prefers_healthiest_switch_target():
    game = make_game()
    player = game.state.players[0]

    player.active_character.receive_damage(8)
    player.characters[1].receive_damage(5)

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.SWITCH_CHARACTER
    assert action.target == 2


def test_cpu_uses_simulation_and_evaluation_to_choose_action(monkeypatch):
    game = make_game()
    cpu = CpuPlayer()
    skill = Action(0, ActionType.ELEMENTAL_SKILL)
    attack = Action(0, ActionType.NORMAL_ATTACK)
    end_round = Action(0, ActionType.END_ROUND)
    legal_actions = [skill, attack, end_round]
    simulated_actions = []

    def fake_simulate_action(current_game, action):
        simulated_actions.append(action)
        return SimpleNamespace(state=SimpleNamespace())

    def fake_evaluate_state(_state, _player_id):
        return {
            skill: 10.0,
            attack: 20.0,
            end_round: -5.0,
        }[simulated_actions[-1]]

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    action = cpu.choose_action(game, 0, legal_actions=legal_actions)

    assert action == attack
    assert simulated_actions == legal_actions
