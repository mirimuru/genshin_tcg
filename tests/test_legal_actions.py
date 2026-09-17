from engine.actions import Action, ActionType
from engine.cards import CardRegistry
from engine.dice import DicePool, DiceType
from engine.game import Game
from engine.legal_actions import LegalActionGenerator
from engine.state import CharacterState, Element, GameState, PlayerState


def make_game():
    players = [
        PlayerState(0, [CharacterState("A", Element.PYRO), CharacterState("B", Element.HYDRO), CharacterState("C", Element.CRYO)]),
        PlayerState(1, [CharacterState("X", Element.PYRO), CharacterState("Y", Element.HYDRO), CharacterState("Z", Element.CRYO)]),
    ]
    game = Game(GameState(players))
    game.execute_action(Action(0, ActionType.REROLL_DICE, target=()))
    game.execute_action(Action(1, ActionType.REROLL_DICE, target=()))
    game.state.players[0].dice = DicePool.default()
    game.state.players[1].dice = DicePool.default()
    return game


def action_types(actions):
    return {action.action_type for action in actions}


def legal(game, player_id=0):
    return LegalActionGenerator.generate(game, player_id)


def test_generates_basic_actions_for_active_character():
    game = make_game()
    actions = legal(game)
    assert action_types(actions) == {
        ActionType.NORMAL_ATTACK,
        ActionType.ELEMENTAL_SKILL,
        ActionType.END_ROUND,
        ActionType.SWITCH_CHARACTER,
    }
    assert {action.target for action in actions if action.action_type is ActionType.SWITCH_CHARACTER} == {1, 2}


def test_elemental_burst_is_available_when_energy_is_full():
    game = make_game()
    character = game.state.players[0].active_character
    character.energy = character.max_energy
    assert ActionType.ELEMENTAL_BURST in action_types(legal(game))


def test_forced_switch_only_allows_switch_actions():
    game = make_game()
    game.state.players[0].active_character.hp = 0
    actions = legal(game)
    assert action_types(actions) == {ActionType.SWITCH_CHARACTER}
    assert {action.target for action in actions} == {1, 2}


def test_switch_is_not_legal_without_dice_when_not_forced():
    game = make_game()
    game.state.players[0].dice = DicePool()
    assert not any(action.action_type is ActionType.SWITCH_CHARACTER for action in legal(game))


def test_card_actions_include_each_legal_target():
    from engine.cards import CardDefinition

    class TargetCard(CardDefinition):
        card_id = "target_card"
        name = "Target Card"
        cost = {DiceType.ANY: 1}

        def get_legal_targets(self, game, player_id):
            return [0, 1]

        def can_play(self, game, player_id, target=None):
            return super().can_play(game, player_id, target) and target in {0, 1}

        def play(self, game, player_id, target=None):
            game.state.players[player_id].active_character_index = target

    registry = CardRegistry([TargetCard()])
    game = make_game()
    game.card_registry = registry
    game.state.players[0].hand = ["target_card"]
    actions = [a for a in legal(game) if a.action_type is ActionType.PLAY_CARD]
    assert actions == [
        Action(0, ActionType.PLAY_CARD, target=0, card_id="target_card"),
        Action(0, ActionType.PLAY_CARD, target=1, card_id="target_card"),
    ]


def test_unplayable_card_is_not_generated_when_cost_is_insufficient():
    from content.cards import INSTRUCTORS_CAP

    game = make_game()
    game.card_registry = CardRegistry([INSTRUCTORS_CAP])
    game.state.players[0].hand = [INSTRUCTORS_CAP.card_id]
    game.state.players[0].dice = DicePool({DiceType.OMNI: 1})
    assert not any(
        action.action_type is ActionType.PLAY_CARD
        and action.card_id == INSTRUCTORS_CAP.card_id
        for action in legal(game)
    )


def test_generated_actions_have_payable_costs():
    game = make_game()
    for action in legal(game):
        if action.action_type in {
            ActionType.NORMAL_ATTACK,
            ActionType.ELEMENTAL_SKILL,
            ActionType.ELEMENTAL_BURST,
            ActionType.SWITCH_CHARACTER,
            ActionType.PLAY_CARD,
        }:
            assert game.state.players[0].dice.can_pay(game.get_action_cost(action))


def test_cpu_selects_from_expanded_legal_actions():
    game = make_game()
    legal_actions = legal(game)
    from players.cpu import CpuPlayer
    action = CpuPlayer().choose_action(game, 0, legal_actions=legal_actions)
    assert action in legal_actions
