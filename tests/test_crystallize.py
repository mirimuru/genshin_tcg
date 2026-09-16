from engine.effects import create_crystallize_shield
from engine.events import DamageEvent
from engine.game import Game
from engine.elemental_reactions import ElementalReaction
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


def test_crystallize_shield_is_applied_by_resolved_damage_event():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target_player.add_combat_status(create_crystallize_shield())

    event = DamageEvent(0, 1, 3, Element.GEO, ElementalReaction.CRYSTALLIZE, resolved=True)
    game._emit_event(event)

    assert target_player.shield == 1
    assert target.hp == 10
    assert target_player.get_combat_status("crystallize_shield") is None


def test_crystallize_creates_one_point_shield_on_active_character():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.PYRO

    game.deal_damage(0, 1, 2, Element.GEO)

    assert target.hp == 7
    assert target_player.shield == 1


def test_crystallize_shield_reduces_incoming_damage_and_is_consumed():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.PYRO
    game.deal_damage(0, 1, 2, Element.GEO)

    game.deal_damage(0, 1, 1, Element.PYRO)

    assert target.hp == 7
    assert target_player.shield == 0


def test_crystallize_shield_is_capped_at_two():
    game = make_game()
    target_player = game.state.players[1]

    assert target_player.add_shield(5) == 2
    assert target_player.shield == 2
    assert target_player.add_shield(1) == 0
    assert target_player.shield == 2


def test_crystallize_shield_follows_the_active_character_after_switch():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.PYRO
    game.deal_damage(0, 1, 2, Element.GEO)

    target_player.switch_character(1)
    new_target = target_player.active_character
    game.deal_damage(0, 1, 1, Element.PYRO)

    assert target_player.shield == 0
    assert target.hp == 7
    assert new_target.hp == 10
