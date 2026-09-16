import pytest

from engine.events import EnergyEvent, EffectContext, GameEvent
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState


class NoOpDefinition:
    def normal_attack(self, game, player_id):
        pass

    def elemental_skill(self, game, player_id):
        pass

    def elemental_burst(self, game, player_id):
        pass


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]
        for character in characters:
            character.definition = NoOpDefinition()
        players.append(PlayerState(player_id, characters))
    return Game(GameState(players))


def test_energy_event_is_game_event():
    event = EnergyEvent(0, 1, 1, "normal_attack")
    assert isinstance(event, GameEvent)
    assert event.player_id == 0
    assert event.character_index == 1
    assert event.amount == 1
    assert event.reason == "normal_attack"
    assert not event.resolved


def test_energy_event_can_represent_burst_energy_consumption():
    event = EnergyEvent(1, 0, -2, "elemental_burst")
    assert event.amount == -2
    assert event.reason == "elemental_burst"


def test_energy_is_bounded_by_character_max_energy():
    character = CharacterState("テスト", Element.PYRO, max_energy=2)
    character.energy = min(character.max_energy, character.energy + 3)
    assert character.energy == 2


def test_energy_event_context_targets_one_character():
    context = EffectContext(owner_id=0, character_index=2)
    event = EnergyEvent(0, 2, 1, "elemental_skill")
    assert context.owner_id == event.player_id
    assert context.character_index == event.character_index


def test_normal_attack_generates_one_energy():
    game = make_game()
    character = game.state.players[0].active_character
    game.normal_attack(0)
    assert character.energy == 1


def test_elemental_skill_generates_one_energy_and_is_capped():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = character.max_energy - 1
    game.elemental_skill(0)
    assert character.energy == character.max_energy


def test_elemental_burst_consumes_all_energy_before_effect():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = character.max_energy
    game.elemental_burst(0)
    assert character.energy == 0


def test_elemental_burst_requires_full_energy():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = character.max_energy - 1
    with pytest.raises(ValueError, match="Energy"):
        game.elemental_burst(0)


def test_change_energy_rejects_negative_result():
    game = make_game()
    with pytest.raises(ValueError, match="Energy"):
        game.change_energy(0, 0, -1, "test")
