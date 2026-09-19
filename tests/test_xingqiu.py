from content.characters.xingqiu import RAIN_SWORD_ID, XINGQIU, Xingqiu
from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.events import ElementalBurstEvent, ElementalSkillEvent, NormalAttackEvent
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [XINGQIU.create_state(), CharacterState("B", Element.PYRO), CharacterState("C", Element.ELECTRO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.active_player_id = 0
    game.state.players[0].dice = DicePool({DiceType.HYDRO: 4})
    return game


def test_xingqiu_definition_has_expected_metadata():
    assert XINGQIU.character_id == "xingqiu"
    assert XINGQIU.name == "行秋"
    assert XINGQIU.element is Element.HYDRO
    assert XINGQIU.max_hp == 10
    assert XINGQIU.max_energy == 2
    assert XINGQIU.weapon_type == "sword"
    assert XINGQIU.elemental_skill_cost == {DiceType.HYDRO: 3}
    assert XINGQIU.elemental_burst_cost == {DiceType.HYDRO: 2}


def test_xingqiu_skill_deals_hydro_damage_and_creates_rain_sword():
    game = make_game()
    game.elemental_skill(0)

    assert game.state.players[1].active_character.hp == 8
    rain_sword = game.state.players[0].get_combat_status(RAIN_SWORD_ID)
    assert rain_sword is not None
    assert rain_sword.usages == 2


def test_rain_sword_triggers_on_next_normal_attack_and_consumes_usage():
    game = make_game()
    game.state.players[0].add_combat_status(Xingqiu.rain_sword())

    game.normal_attack(0)

    assert game.state.players[1].active_character.hp == 6
    rain_sword = game.state.players[0].get_combat_status(RAIN_SWORD_ID)
    assert rain_sword is not None
    assert rain_sword.usages == 1


def test_rain_sword_does_not_trigger_on_other_player_attack():
    game = make_game()
    game.state.players[0].add_combat_status(Xingqiu.rain_sword())
    game.state.active_player_id = 1

    game.normal_attack(1)

    rain_sword = game.state.players[0].get_combat_status(RAIN_SWORD_ID)
    assert rain_sword is not None
    assert rain_sword.usages == 2


def test_xingqiu_burst_deals_hydro_damage_and_creates_rain_sword():
    game = make_game()
    game.state.players[0].active_character.energy = 2

    game.elemental_burst(0)

    assert game.state.players[1].active_character.hp == 9
    assert game.state.players[0].active_character.energy == 0
    rain_sword = game.state.players[0].get_combat_status(RAIN_SWORD_ID)
    assert rain_sword is not None
    assert rain_sword.usages == 2
