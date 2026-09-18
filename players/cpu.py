from engine.actions import Action, ActionType
from engine.dice import DiceType
from engine.evaluation import evaluate_state
from engine.simulation import expected_value, simulate_action, simulate_roll
from engine.state import GamePhase


class CpuPlayer:
    """合法手を探索・シミュレーションし、状態評価で行動を選択するCPU。"""

    LOW_HP_THRESHOLD = 3
    SEARCH_DEPTH = 2
    DEFAULT_MAX_SEARCH_NODES = 10_000
    ACTION_TIE_BREAK = {
        ActionType.ELEMENTAL_BURST: 4,
        ActionType.ELEMENTAL_SKILL: 3,
        ActionType.NORMAL_ATTACK: 2,
        ActionType.PLAY_CARD: 2,
        ActionType.SWITCH_CHARACTER: 1,
        ActionType.ELEMENTAL_TUNING: 0,
        ActionType.END_ROUND: -1,
    }

    def __init__(self, search_depth=None, max_search_nodes=None):
        self.search_depth = self.SEARCH_DEPTH if search_depth is None else search_depth
        self.max_search_nodes = (
            self.DEFAULT_MAX_SEARCH_NODES
            if max_search_nodes is None
            else max_search_nodes
        )
        if self.search_depth <= 0:
            raise ValueError("search_depth must be positive")
        if self.max_search_nodes <= 0:
            raise ValueError("max_search_nodes must be positive")
        self.last_search_nodes = 0

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
            key=lambda action: (
                self._evaluate_action(game, player_id, action, self.search_depth),
                self.ACTION_TIE_BREAK.get(action.action_type, 0),
            ),
        )

    def _evaluate_action(self, game, player_id, action, depth=None) -> float:
        """Actionを仮想実行し、指定深度まで相手の応答を含めて評価する。"""
        if depth is None:
            depth = self.search_depth
        simulated_game = simulate_action(game, action)
        self.last_search_nodes = 0
        return self._search_value(
            simulated_game,
            player_id,
            1 - player_id,
            depth - 1,
        )

    def _evaluate_chance_roll(self, game, player_id, depth=None) -> float:
        """ダイスロールをChance Nodeとして展開し、各結果の期待評価値を返す。"""
        if depth is None:
            depth = self.search_depth
        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, player_id)

        outcomes = simulate_roll(game, player_id)
        if not outcomes:
            return evaluate_state(game.state, player_id)

        return expected_value(
            outcomes,
            lambda outcome: self._search_node(
                outcome,
                player_id,
                player_id,
                depth - 1,
                float("-inf"),
                float("inf"),
            ),
        )

    def _search_value(self, game, root_player_id, current_player_id, depth, alpha=float("-inf"), beta=float("inf")) -> float:
        """ノード上限付きalpha-beta探索。ノード数はこの探索単位でリセットされる。"""
        self.last_search_nodes = 0
        return self._search_node(
            game,
            root_player_id,
            current_player_id,
            depth,
            alpha,
            beta,
        )

    def _search_node(self, game, root_player_id, current_player_id, depth, alpha, beta) -> float:
        if self.last_search_nodes >= self.max_search_nodes:
            return evaluate_state(game.state, root_player_id)
        self.last_search_nodes += 1

        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, root_player_id)

        legal_actions = game.get_legal_actions(current_player_id)
        if not legal_actions:
            return evaluate_state(game.state, root_player_id)

        if current_player_id == root_player_id:
            value = float("-inf")
            for action in legal_actions:
                value = max(
                    value,
                    self._search_node(
                        simulate_action(game, action),
                        root_player_id,
                        1 - current_player_id,
                        depth - 1,
                        alpha,
                        beta,
                    ),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = float("inf")
        for action in legal_actions:
            value = min(
                value,
                self._search_node(
                    simulate_action(game, action),
                    root_player_id,
                    1 - current_player_id,
                    depth - 1,
                    alpha,
                    beta,
                ),
            )
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    @classmethod
    def _minimax(
        cls,
        game,
        root_player_id,
        current_player_id,
        depth,
        alpha=float("-inf"),
        beta=float("inf"),
    ) -> float:
        """後方互換用のalpha-beta minimax探索。"""
        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, root_player_id)

        legal_actions = game.get_legal_actions(current_player_id)
        if not legal_actions:
            return evaluate_state(game.state, root_player_id)

        if current_player_id == root_player_id:
            value = float("-inf")
            for action in legal_actions:
                value = max(
                    value,
                    cls._minimax(
                        simulate_action(game, action),
                        root_player_id,
                        1 - current_player_id,
                        depth - 1,
                        alpha,
                        beta,
                    ),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = float("inf")
        for action in legal_actions:
            value = min(
                value,
                cls._minimax(
                    simulate_action(game, action),
                    root_player_id,
                    1 - current_player_id,
                    depth - 1,
                    alpha,
                    beta,
                ),
            )
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    @staticmethod
    def _choose_reroll(game, player_id, legal_actions) -> Action:
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
