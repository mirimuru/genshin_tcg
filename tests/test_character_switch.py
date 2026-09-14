import pytest

from engine.state import CharacterState, Element, GameState, PlayerState


def make_player(player_id: int = 0) -> PlayerState:
    return PlayerState(
        player_id=player_id,
        characters=[
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ],
    )


def make_game() -> GameState:
    return GameState([
        make_player(0),
        make_player(1),
    ])


def test_switch_character_changes_active_character():
    player = make_player()

    assert player.active_character_index == 0

    player.switch_character(1)

    assert player.active_character_index == 1
    assert player.active_character.name == "キャラクター2"


def test_cannot_switch_to_same_character():
    player = make_player()

    with pytest.raises(ValueError, match="すでにアクティブ"):
        player.switch_character(0)


def test_cannot_switch_to_defeated_character():
    player = make_player()
    player.characters[1].receive_damage(999)

    assert not player.characters[1].alive
    assert not player.can_switch_to(1)

    with pytest.raises(ValueError, match="戦闘不能"):
        player.switch_character(1)


def test_cannot_switch_to_invalid_index():
    player = make_player()

    with pytest.raises(ValueError, match="存在しない"):
        player.switch_character(3)

    with pytest.raises(ValueError, match="存在しない"):
        player.switch_character(-1)


def test_requires_switch_when_active_character_is_defeated():
    player = make_player()

    assert not player.requires_switch
    assert not player.defeated

    player.active_character.receive_damage(999)

    assert not player.active_character.alive
    assert player.requires_switch
    assert not player.defeated


def test_player_is_defeated_when_all_characters_are_defeated():
    player = make_player()

    for character in player.characters:
        character.receive_damage(999)

    assert player.defeated


def test_game_over_and_winner_are_detected():
    game = make_game()

    for character in game.players[1].characters:
        character.receive_damage(999)

    assert game.check_game_over()
    assert game.game_over
    assert game.winner == 0


def test_game_is_not_over_while_both_players_have_living_characters():
    game = make_game()

    assert not game.check_game_over()
    assert not game.game_over
    assert game.winner is None


def test_alive_character_indices():
    player = make_player()

    player.characters[0].receive_damage(999)

    assert player.alive_character_indices() == [1, 2]
