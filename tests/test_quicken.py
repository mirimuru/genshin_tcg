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


def test_quicken_creates_two_usage_catalyzing_field():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.ELECTRO

    game.deal_damage(0, 1, 2, Element.DENDRO)

    assert game.state.players[0].catalyzing_field == 2
    assert target.hp == 7
    assert target.elemental_aura is None


def test_catalyzing_field_boosts_next_two_dendro_or_electro_damage_instances():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.ELECTRO

    # ゲーム終了条件は3キャラクター全員の戦闘不能なので、
    # 最後の攻撃でこのキャラクターを倒したときにゲーム終了になるようにする。
    target_player.characters[1].receive_damage(999)
    target_player.characters[2].receive_damage(999)

    game.deal_damage(0, 1, 2, Element.DENDRO)

    game.deal_damage(0, 1, 2, Element.ELECTRO)
    assert target.hp == 4
    assert game.state.players[0].catalyzing_field == 1

    game.deal_damage(0, 1, 2, Element.DENDRO)
    assert target.hp == 1
    assert game.state.players[0].catalyzing_field == 0

    game.deal_damage(0, 1, 2, Element.ELECTRO)
    assert target.hp == 0
    assert game.state.game_over


def test_catalyzing_field_is_not_consumed_by_other_elements():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.ELECTRO
    game.deal_damage(0, 1, 2, Element.DENDRO)

    game.deal_damage(0, 1, 2, Element.PYRO)

    assert game.state.players[0].catalyzing_field == 2


def test_catalyzing_field_follows_active_character_when_switching():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.ELECTRO
    game.deal_damage(0, 1, 2, Element.DENDRO)

    game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=1))
    assert game.state.players[0].catalyzing_field == 2

    game.deal_damage(0, 1, 2, Element.ELECTRO)
    assert target.hp == 4
    assert game.state.players[0].catalyzing_field == 1
