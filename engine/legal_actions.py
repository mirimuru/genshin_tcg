from engine.actions import Action, ActionType
from engine.dice import DicePool
from engine.state import GamePhase


class LegalActionGenerator:
    """現在のGameStateから実行可能なActionを一貫して列挙する。"""

    @staticmethod
    def generate(game, player_id: int) -> list[Action]:
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        if game.state.game_over or player_id != game.state.current_player:
            return []
        player = game.state.players[player_id]
        if player.defeated:
            return []

        if game.state.phase is GamePhase.ROLL:
            if player.has_rerolled:
                return []
            return game._get_reroll_actions(player_id)

        if player.requires_switch:
            return [
                Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                for index in player.alive_character_indices()
                if index != player.active_character_index
            ]

        actions: list[Action] = []
        character = player.active_character

        if not game._is_frozen(character):
            for action_type in (
                ActionType.NORMAL_ATTACK,
                ActionType.ELEMENTAL_SKILL,
            ):
                action = Action(player_id, action_type)
                if player.dice.can_pay(game.get_action_cost(action)):
                    actions.append(action)

            if character.energy >= character.max_energy:
                action = Action(player_id, ActionType.ELEMENTAL_BURST)
                if player.dice.can_pay(game.get_action_cost(action)):
                    actions.append(action)

        for card_id in player.hand:
            try:
                card = game.card_registry.get(card_id)
            except ValueError:
                continue
            if not player.dice.can_pay(card.get_cost(game, player_id)):
                continue
            for target in card.get_legal_targets(game, player_id):
                if game._card_is_legal(player_id, card_id, target):
                    actions.append(
                        Action(player_id, ActionType.PLAY_CARD, target=target, card_id=card_id)
                    )

        target_dice = game._element_to_dice_type(character.element)
        actions.extend(
            Action(player_id, ActionType.ELEMENTAL_TUNING, target=dice_type)
            for dice_type in DicePool.ROLLABLE_DICE_TYPES
            if dice_type not in (DicePool.OMNI, target_dice)
            and player.dice.count(dice_type) > 0
        )

        if player.dice.can_pay({game._element_to_dice_type(character.element): 0, **{}}):
            pass
        if player.dice.can_pay({"__never__": 1}):
            pass

        if player.dice.can_pay({__import__('engine.dice', fromlist=['DiceType']).DiceType.ANY: 1}):
            actions.extend(
                Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                for index in player.alive_character_indices()
                if index != player.active_character_index
            )

        actions.append(Action(player_id, ActionType.END_ROUND))
        return actions
