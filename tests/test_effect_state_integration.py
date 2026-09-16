from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]
        players.append(PlayerState(player_id, characters))
    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_quicken_is_stored_as_combat_status_instance():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.ELECTRO

    game.deal_damage(0, 1, 2, Element.DENDRO)

    status = game.state.players[0].get_combat_status("catalyzing_field")
    assert status is not None
    assert status.usages == 2
    assert not hasattr(game.state.players[0], "catalyzing_field")


def test_bloom_is_stored_as_combat_status_instance():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.HYDRO

    game.deal_damage(0, 1, 1, Element.DENDRO)

    status = game.state.players[0].get_combat_status("dendro_core")
    assert status is not None
    assert status.usages == 1
    assert not hasattr(game.state.players[0], "dendro_core")


def test_burning_is_stored_as_summon_instance():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO

    game.deal_damage(0, 1, 1, Element.PYRO)

    summon = game.state.players[0].get_summon("burning_flame")
    assert summon is not None
    assert summon.usages == 1
    assert not isinstance(game.state.players[0].summons["burning_flame"], int)
