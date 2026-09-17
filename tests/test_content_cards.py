import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.state import CharacterState, Element, GamePhase, GameState, PlayerState
from content.cards import SWEET_MADAME, SweetMadame
from engine.cards import CardRegistry


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.state.phase = GamePhase.ACTION
    game.state.current_player = 0
    players[0].dice = DicePool({DiceType.OMNI: 2})
    players[1].dice = DicePool({DiceType.OMNI: 2})
    return game


def test_sweet_madame_has_stable_definition():
    assert isinstance(SWEET_MADAME, SweetMadame)
    assert SWEET_MADAME.card_id == "sweet_madame"
    assert SWEET_MADAME.name == "モンド風ハッシュドポテト"
    assert SWEET_MADAME.cost == {DiceType.ANY: 1}


def test_sweet_madame_heals_active_character_and_is_registered():
    game = make_game()
    game.card_registry = CardRegistry([SWEET_MADAME])
    player = game.state.players[0]
    player.hand = ["sweet_madame"]
    player.active_character.hp = 5

    game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="sweet_madame"))

    assert player.active_character.hp == 6
    assert player.hand == []
    assert player.dice.total == 1


def test_sweet_madame_cannot_be_played_at_full_hp():
    game = make_game()
    game.card_registry = CardRegistry([SWEET_MADAME])
    player = game.state.players[0]
    player.hand = ["sweet_madame"]
    player.active_character.hp = player.active_character.max_hp

    with pytest.raises(ValueError, match="使用できません"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="sweet_madame"))

    assert player.hand == ["sweet_madame"]
    assert player.dice.total == 2
