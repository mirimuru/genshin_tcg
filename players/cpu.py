from engine.actions import Action, ActionType
from engine.dice import DiceType
from engine.evaluation import evaluate_state
from engine.simulation import simulate_action
from engine.state import GamePhase


class CpuPlayer:
    """合法手をシミュレーションし、状態評価で行動を選択するCPU。"""

    LOW_HP_THRESHOLD = 3

    def choose_action(self, game, player_id: int, legal_actions=None) -> Action:
        if legal_actions is None:
            legal_actions = game.get_legal_actions(player_id)
        if not legal_actions:
            return Action(player_id, ActionType.END_ROUND)

        if game.state.phase is GamePhase.ROLL:
            return self._choose_reroll(game, player_id, legal_actions)

        switch_actions = [
            action for action in legal_actions
            if action.action_type is ActionType.SWITCH_CHARACTER
        ]
        player = game.state.players[player_id]

        if player.requires_switch and switch_actions:
            return self._best_switch_action(player, switch_actions)

        burst = next(
            (action for action in legal_actions if action.action_type is ActionType.ELEMENTAL_BURST),
            None,
        )
        if burst is not None:
            return burst

        if player.active_character.hp <= self.LOW_HP_THRESHOLD and switch_actions:
            return self._best_switch_action(player, switch_actions)

        return max(
            legal_actions,
            key=lambda action: self._evaluate_action(game, player_id, action),
        )

    @staticmethod
    def _evaluate_action(game, player_id: int, action: Action) -> float:
        """Actionを仮想実行し、結果状態をCPU視点で評価する。"""
        simulated_game = simulate_action(game, action)
        return evaluate_state(simulated_game.state, player_id)

    @staticmethod
    def _choose_reroll(game, player_id: int, legal_actions) -> Action:
        player = game.state.players[player_id]
        target_dice = game._element_to_dice_type(player.active_character.element)

        def score(action):
            selected = action.target or ()
            return sum(
                1
                for dice_type in selected
                if dice_type not in (DiceType.OMNI, target_dice)
            )

        return max(legal_actions, key=score)

    @staticmethod
    def _best_switch_action(player, actions):
        return max(
            actions,
            key=lambda action: (
                player.characters[action.target].hp / player.characters[action.target].max_hp,
                player.characters[action.target].hp,
            ),
        )
