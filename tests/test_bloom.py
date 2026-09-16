from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState


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
    game.state.phase = GamePhase.ACTION
    return game


def test_bloom_creates_one_dendro_core_for_attacker():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.HYDRO

    game.deal_damage(0, 1, 1, Element.DENDRO)

    assert game.state.players[0].dendro_core == 1


def test_dendro_core_boosts_next_pyro_or_electro_damage_by_two():
    game = make_game()
    attacker = game.state.players[0]
    target = game.state.players[1].active_character
    attacker.dendro_core = 1

    game.deal_damage(0, 1, 1, Element.PYRO)

    assert target.hp == 7
    assert attacker.dendro_core == 0


def test_dendro_core_is_not_consumed_by_other_elements():
    game = make_game()
    attacker = game.state.players[0]
    target = game.state.players[1].active_character
    attacker.dendro_core = 1

    game.deal_damage(0, 1, 1, Element.CRYO)

    assert target.hp == 9
    assert attacker.dendro_core == 1


def test_bloom_stacks_dendro_core_up_to_two():
    game = make_game()
    target = game.state.players[1].active_character

    target.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 1, Element.DENDRO)
    target.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 1, Element.DENDRO)

    assert game.state.players[0].dendro_core == 2

    target.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 1, Element.DENDRO)
    assert game.state.players[0].dendro_core == 2
