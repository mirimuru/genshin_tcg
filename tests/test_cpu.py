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
        return SimpleNamespace(
            state=SimpleNamespace(game_over=False),
            get_legal_actions=lambda _player_id: [],
        )

    def fake_evaluate_state(_state, _player_id):
        action = simulated_actions[-1]
        if action is skill:
            return 10.0
        if action is attack:
            return 20.0
        return -5.0

    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    action = cpu.choose_action(game, 0, legal_actions=legal_actions)

    assert action == attack
    assert simulated_actions == legal_actions


def test_cpu_looks_ahead_to_opponent_response(monkeypatch):
    game = make_game()
    cpu = CpuPlayer()
    attack = Action(0, ActionType.NORMAL_ATTACK)
    skill = Action(0, ActionType.ELEMENTAL_SKILL)
    opponent_attack = Action(1, ActionType.NORMAL_ATTACK)
    opponent_switch = Action(1, ActionType.SWITCH_CHARACTER, target=1)
    opponent_end = Action(1, ActionType.END_ROUND)
    simulations = []

    root_states = {
        "normal_attack": SimpleNamespace(name="attack_state", game_over=False),
        "elemental_skill": SimpleNamespace(name="skill_state", game_over=False),
    }
    response_states = {
        ("attack_state", opponent_attack): SimpleNamespace(name="attack_after_attack", game_over=False),
        ("attack_state", opponent_switch): SimpleNamespace(name="attack_after_switch", game_over=False),
        ("skill_state", opponent_end): SimpleNamespace(name="skill_after_end", game_over=False),
    }

    def fake_simulate_action(current_game, action):
        simulations.append(action)
        if action.player_id == 0:
            state = root_states[action.action_type.value]
            responses = {
                "attack_state": [opponent_attack, opponent_switch],
                "skill_state": [opponent_end],
            }[state.name]
        else:
            state = response_states[(current_game.state.name, action)]
            responses = []
        return SimpleNamespace(
            state=state,
            get_legal_actions=lambda _player_id, responses=responses: responses,
        )

    scores = {
        "attack_after_attack": 50.0,
        "attack_after_switch": -20.0,
        "skill_after_end": 5.0,
    }

    def fake_evaluate_state(state, _player_id):
        return scores[state.name]

    game.state.name = "root"
    monkeypatch.setattr("players.cpu.simulate_action", fake_simulate_action)
    monkeypatch.setattr("players.cpu.evaluate_state", fake_evaluate_state)

    action = cpu.choose_action(game, 0, legal_actions=[attack, skill])

    assert action is skill
    assert simulations == [attack, opponent_attack, opponent_switch, skill, opponent_end]
