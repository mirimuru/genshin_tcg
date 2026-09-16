from content.characters.kaeya import KAEYA
from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [KAEYA.create_state(), CharacterState("控え1", Element.HYDRO), CharacterState("控え2", Element.PYRO)]),
        PlayerState(1, [CharacterState("相手1", Element.PYRO), CharacterState("相手2", Element.ELECTRO), CharacterState("相手3", Element.GEO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    return game


def switch(game, player_id, target):
    game.state.current_player = player_id
    game.state.players[player_id].dice = DicePool({DiceType.OMNI: 8})
    game.execute_action(Action(player_id, ActionType.SWITCH_CHARACTER, target=target))


def test_kaeya_has_official_stats_and_costs():
    state = KAEYA.create_state()
    assert state.max_hp == 10
    assert state.max_energy == 2
    assert KAEYA.normal_attack_cost == {DiceType.CRYO: 1, DiceType.ANY: 2}
    assert KAEYA.elemental_skill_cost == {DiceType.CRYO: 3}
    assert KAEYA.elemental_burst_cost == {DiceType.CRYO: 4}


def test_kaeya_burst_creates_icicle():
    game = make_game()
    game.state.players[0].active_character.energy = 2

    game.elemental_burst(0)

    icicle = game.state.players[0].get_combat_status("kaeya_icicle")
    assert icicle is not None
    assert icicle.usages == 3
    assert game.state.players[1].active_character.hp == 9


def test_icicle_deals_two_cryo_after_own_character_switch():
    game = make_game()
    game.state.players[0].active_character.energy = 2
    game.elemental_burst(0)
    target = game.state.players[1].active_character

    switch(game, 0, 1)

    assert target.hp == 7
    assert game.state.players[0].get_combat_status("kaeya_icicle").usages == 2


def test_icicle_does_not_trigger_on_opponent_switch():
    game = make_game()
    game.state.players[0].active_character.energy = 2
    game.elemental_burst(0)
    target = game.state.players[1].active_character

    switch(game, 1, 1)

    assert target.hp == 9
    assert game.state.players[0].get_combat_status("kaeya_icicle").usages == 3


def test_icicle_expires_after_three_switches():
    game = make_game()
    game.state.players[0].active_character.energy = 2
    game.elemental_burst(0)
    target = game.state.players[1].active_character

    switch(game, 0, 1)
    switch(game, 0, 0)
    switch(game, 0, 1)

    assert target.hp == 3
    assert game.state.players[0].get_combat_status("kaeya_icicle") is None
