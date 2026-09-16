import pytest

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.effects import create_dendro_core
from engine.game import Game
from engine.state import CharacterDefinition, CharacterRegistry, CharacterState, Element, GameState, PlayerState


class RecordingDefinition:
    def __init__(self):
        self.calls = []

    def normal_attack(self, game, player_id):
        self.calls.append(("normal_attack", player_id))

    def elemental_skill(self, game, player_id):
        self.calls.append(("elemental_skill", player_id))

    def elemental_burst(self, game, player_id):
        self.calls.append(("elemental_burst", player_id))


def make_game():
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("キャラクター1", Element.PYRO),
            CharacterState("キャラクター2", Element.HYDRO),
            CharacterState("キャラクター3", Element.CRYO),
        ]
        for character in characters:
            character.definition = RecordingDefinition()
        players.append(PlayerState(player_id, characters))

    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def test_character_state_has_definition_by_default():
    character = CharacterState("テストキャラ", Element.PYRO, max_hp=12, max_energy=3)
    assert character.definition.character_id == "legacy:テストキャラ"
    assert character.definition.name == "テストキャラ"
    assert character.definition.element is Element.PYRO
    assert character.definition.max_hp == 12
    assert character.definition.max_energy == 3


def test_character_state_can_be_created_from_definition():
    definition = CharacterDefinition("test_character", "定義キャラ", Element.HYDRO, max_hp=8, max_energy=1)
    character = CharacterState("ignored", Element.PYRO, definition=definition)
    assert character.definition is definition
    assert character.name == "定義キャラ"
    assert character.element is Element.HYDRO
    assert character.max_hp == 8
    assert character.max_energy == 1
    assert character.hp == 8


def test_character_registry_resolves_definitions():
    pyro = CharacterDefinition("pyro_test", "炎テスト", Element.PYRO)
    hydro = CharacterDefinition("hydro_test", "水テスト", Element.HYDRO)
    registry = CharacterRegistry([pyro, hydro])
    assert registry.get("pyro_test") is pyro
    assert registry.contains("hydro_test")
    assert [definition.character_id for definition in registry] == ["pyro_test", "hydro_test"]


def test_character_registry_rejects_duplicate_ids():
    definition = CharacterDefinition("duplicate", "重複1", Element.PYRO)
    registry = CharacterRegistry([definition])
    with pytest.raises(ValueError, match="重複"):
        registry.register(CharacterDefinition("duplicate", "重複2", Element.HYDRO))


def test_character_registry_rejects_unknown_character():
    registry = CharacterRegistry()
    with pytest.raises(ValueError, match="未登録のキャラクター"):
        registry.get("unknown")


def test_game_uses_character_definition_without_manual_assignment():
    definition = CharacterDefinition("pyro_test", "炎テスト", Element.PYRO)
    players = []
    for player_id in (0, 1):
        characters = [
            CharacterState("unused", Element.HYDRO, definition=definition),
            CharacterState("控え1", Element.HYDRO),
            CharacterState("控え2", Element.CRYO),
        ]
        players.append(PlayerState(player_id, characters))
    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()

    target = game.state.players[1].active_character
    game.execute_action(Action(0, ActionType.NORMAL_ATTACK))

    assert target.hp == 8
    assert game.state.players[0].active_character.energy == 1


def test_execute_action_dispatches_normal_attack():
    game = make_game()
    game.execute_action(Action(0, ActionType.NORMAL_ATTACK))
    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("normal_attack", 0)]
    assert game.state.current_player == 1


def test_execute_action_dispatches_elemental_skill():
    game = make_game()
    game.execute_action(Action(0, ActionType.ELEMENTAL_SKILL))
    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("elemental_skill", 0)]
    assert game.state.current_player == 1


def test_execute_action_dispatches_elemental_burst():
    game = make_game()
    game.state.players[0].active_character.energy = 2
    game.execute_action(Action(0, ActionType.ELEMENTAL_BURST))
    definition = game.state.players[0].characters[0].definition
    assert definition.calls == [("elemental_burst", 0)]
    assert game.state.current_player == 1


def test_execute_action_switches_character():
    game = make_game()
    game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=1))
    assert game.state.players[0].active_character_index == 1
    assert game.state.current_player == 1


def test_execute_action_rejects_invalid_switch_target():
    game = make_game()
    with pytest.raises(ValueError, match="交代"):
        game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=0))


def test_execute_action_requires_current_player():
    game = make_game()
    with pytest.raises(ValueError, match="現在のプレイヤー"):
        game.execute_action(Action(1, ActionType.NORMAL_ATTACK))


def test_execute_action_requires_forced_switch():
    game = make_game()
    game.state.players[0].active_character.receive_damage(999)
    with pytest.raises(ValueError, match="強制交代"):
        game.execute_action(Action(0, ActionType.NORMAL_ATTACK))


def test_execute_action_forced_switch_is_allowed():
    game = make_game()
    game.state.players[0].active_character.receive_damage(999)
    game.execute_action(Action(0, ActionType.SWITCH_CHARACTER, target=1))
    assert game.state.players[0].active_character_index == 1


def test_end_round_passes_turn_to_opponent():
    game = make_game()
    game.execute_action(Action(0, ActionType.END_ROUND))
    assert game.state.players[0].has_ended_round
    assert game.state.current_player == 1
    assert game.state.round_number == 1


def test_end_round_starts_next_round_when_both_players_ended():
    game = make_game()
    game.execute_action(Action(0, ActionType.END_ROUND))
    game.execute_action(Action(1, ActionType.END_ROUND))
    assert game.state.round_number == 2
    assert game.state.current_player == 0
    assert game.state.phase.value == "roll"
    assert not game.state.players[0].has_ended_round
    assert not game.state.players[1].has_ended_round


def test_execute_action_rejects_actions_after_game_over():
    game = make_game()
    for character in game.state.players[1].characters:
        character.receive_damage(999)
    game.state.check_game_over()
    with pytest.raises(ValueError, match="ゲーム終了"):
        game.execute_action(Action(0, ActionType.END_ROUND))


def test_play_card_is_not_implemented_yet():
    game = make_game()
    with pytest.raises(NotImplementedError, match="カード"):
        game.execute_action(Action(0, ActionType.PLAY_CARD, card_id="test_card"))


def test_deal_damage_applies_vaporize_bonus_and_consumes_aura():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 2, Element.PYRO)
    assert target.hp == 6
    assert target.elemental_aura is None


def test_deal_damage_applies_overloaded_bonus():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.ELECTRO
    game.deal_damage(0, 1, 2, Element.PYRO)
    assert target.hp == 6
    assert target.elemental_aura is None


def test_overloaded_requires_opponent_to_switch():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.ELECTRO
    game.deal_damage(0, 1, 1, Element.PYRO)
    assert target.hp == 7
    assert target_player.requires_switch


def test_forced_switch_clears_overloaded_switch_requirement():
    game = make_game()
    target_player = game.state.players[1]
    target_player.active_character.elemental_aura = Element.ELECTRO
    game.deal_damage(0, 1, 1, Element.PYRO)
    game.state.current_player = 1
    game.execute_action(Action(1, ActionType.SWITCH_CHARACTER, target=1))
    assert target_player.active_character_index == 1
    assert not target_player.requires_switch


def test_deal_damage_applies_bloom_bonus():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 2, Element.HYDRO)
    assert target.hp == 7
    assert target.elemental_aura is None


def test_bloom_creates_dendro_core_for_attacker():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 2, Element.HYDRO)
    assert game.state.players[0].get_combat_status("dendro_core").usages == 1


def test_dendro_core_boosts_next_pyro_damage_and_is_consumed():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.HYDRO)
    assert game.state.players[0].get_combat_status("dendro_core").usages == 1
    target.elemental_aura = None
    hp_before = target.hp
    game.deal_damage(0, 1, 1, Element.PYRO)
    assert hp_before - target.hp == 3
    assert game.state.players[0].get_combat_status("dendro_core") is None


def test_dendro_core_is_capped_at_two():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.HYDRO)
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.HYDRO)
    assert game.state.players[0].get_combat_status("dendro_core").usages == 2
    target.elemental_aura = Element.DENDRO
    game.deal_damage(0, 1, 1, Element.HYDRO)
    assert game.state.players[0].get_combat_status("dendro_core").usages == 2


def test_dendro_core_boosts_electro_damage_and_is_consumed():
    game = make_game()
    attacker = game.state.players[0]
    target = game.state.players[1].active_character
    attacker.add_combat_status(create_dendro_core(1))
    target.elemental_aura = None
    hp_before = target.hp
    game.deal_damage(0, 1, 1, Element.ELECTRO)
    assert hp_before - target.hp == 3
    assert attacker.get_combat_status("dendro_core") is None


def test_dendro_core_is_not_consumed_by_non_pyro_or_electro_damage():
    game = make_game()
    attacker = game.state.players[0]
    target = game.state.players[1].active_character
    attacker.add_combat_status(create_dendro_core(1))
    target.elemental_aura = None
    game.deal_damage(0, 1, 1, Element.HYDRO)
    assert attacker.get_combat_status("dendro_core").usages == 1


def test_deal_damage_applies_electro_charged_bonus():
    game = make_game()
    target = game.state.players[1].active_character
    target.elemental_aura = Element.HYDRO
    game.deal_damage(0, 1, 2, Element.ELECTRO)
    assert target.hp == 7
    assert target.elemental_aura is None


def test_electro_charged_deals_one_damage_to_other_alive_characters():
    game = make_game()
    target_player = game.state.players[1]
    target = target_player.active_character
    target.elemental_aura = Element.HYDRO
    reserve_1 = target_player.characters[1]
    reserve_2 = target_player.characters[2]
    hp_1 = reserve_1.hp
    hp_2 = reserve_2.hp
    game.deal_damage(0, 1, 2, Element.ELECTRO)
    assert target.hp == 7
    assert reserve_1.hp == hp_1 - 1
    assert reserve_2.hp == hp_2 - 1
