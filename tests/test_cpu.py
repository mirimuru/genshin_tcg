from engine.actions import ActionType
from engine.state import CharacterState, Element, GameState, PlayerState
from players.cpu import CpuPlayer


def make_player(player_id=0):
    return PlayerState(
        player_id=player_id,
        characters=[
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ],
    )


def make_game():
    return GameState([make_player(0), make_player(1)])


def test_cpu_uses_burst_when_energy_is_full():
    game = make_game()
    game.players[0].active_character.energy = 2

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.ELEMENTAL_BURST
    assert action.player_id == 0


def test_cpu_switches_when_active_character_is_defeated():
    game = make_game()
    game.players[0].active_character.receive_damage(999)

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.SWITCH_CHARACTER
    assert action.target == 1


def test_cpu_switches_from_low_hp_character():
    game = make_game()
    game.players[0].active_character.receive_damage(8)

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
    player = game.players[0]
    player.active_character.receive_damage(8)
    player.characters[1].receive_damage(5)

    action = CpuPlayer().choose_action(game, 0)

    assert action.action_type is ActionType.SWITCH_CHARACTER
    assert action.target == 2
