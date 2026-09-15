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


def test_swirl_spreads_aura_element_to_all_standby_characters():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.PYRO

    game.deal_damage(0, 1, 2, Element.ANEMO)

    assert target.hp == 7
    assert target_player.characters[1].hp == 9
    assert target_player.characters[2].hp == 9
    assert target_player.characters[1].elemental_aura is Element.PYRO
    assert target_player.characters[2].elemental_aura is Element.PYRO


def test_swirl_does_not_damage_defeated_standby_characters():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.PYRO
    target_player.characters[1].receive_damage(999)

    game.deal_damage(0, 1, 2, Element.ANEMO)

    assert target_player.characters[1].hp == 0
    assert target_player.characters[2].hp == 9
