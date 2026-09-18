from engine.actions import Action, ActionType
from engine.dice import DiceType
from engine.evaluation import evaluate_state
from engine.simulation import expected_value, sample_round_roll, simulate_action, simulate_reroll, simulate_roll
from engine.state import GamePhase


class CpuPlayer:
    """合法手を探索・シミュレーションし、状態評価で行動を選択するCPU。"""

    LOW_HP_THRESHOLD = 3
    SEARCH_DEPTH = 2
    DEFAULT_MAX_SEARCH_NODES = 10_000
    MAX_REROLL_CANDIDATES = 16
    ROUND_ROLL_SAMPLES = 64
    ACTION_TIE_BREAK = {
        ActionType.ELEMENTAL_BURST: 4,
        ActionType.ELEMENTAL_SKILL: 3,
        ActionType.NORMAL_ATTACK: 2,
        ActionType.PLAY_CARD: 2,
        ActionType.SWITCH_CHARACTER: 1,
        ActionType.ELEMENTAL_TUNING: 0,
        ActionType.END_ROUND: -1,
    }

    def __init__(self, search_depth=None, max_search_nodes=None, round_roll_samples=None):
        self.search_depth = self.SEARCH_DEPTH if search_depth is None else search_depth
        self.max_search_nodes = self.DEFAULT_MAX_SEARCH_NODES if max_search_nodes is None else max_search_nodes
        self.round_roll_samples = self.ROUND_ROLL_SAMPLES if round_roll_samples is None else round_roll_samples
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
        if getattr(game.state, "phase", None) is GamePhase.ROLL:
            return self._choose_reroll(game, player_id, legal_actions)

        switch_actions = [a for a in legal_actions if a.action_type is ActionType.SWITCH_CHARACTER]
        player = game.state.players[player_id]
        if player.requires_switch and switch_actions:
            return self._best_switch_action(player, switch_actions)
        burst = next((a for a in legal_actions if a.action_type is ActionType.ELEMENTAL_BURST), None)
        if burst is not None:
            return burst
        if player.active_character.hp <= self.LOW_HP_THRESHOLD and switch_actions:
            return self._best_switch_action(player, switch_actions)
        return max(legal_actions, key=lambda action: (
            self._evaluate_action(game, player_id, action, self.search_depth),
            self.ACTION_TIE_BREAK.get(action.action_type, 0),
        ))

    def _evaluate_action(self, game, player_id, action, depth=None) -> float:
        if depth is None:
            depth = self.search_depth
        simulated_game = simulate_action(game, action)
        self.last_search_nodes = 0
        if (
            action.action_type is ActionType.END_ROUND
            and getattr(simulated_game.state, "phase", None) is GamePhase.ROLL
        ):
            return self._evaluate_round_roll(simulated_game, player_id, depth - 1)
        return self._search_value(simulated_game, player_id, 1 - player_id, depth - 1)

    def _evaluate_round_roll(self, game, player_id, depth) -> float:
        """次ラウンドの両者のダイス生成をChance Nodeとして評価する。

        8個×2人の全組合せは巨大になるため、CPU探索では固定seedの
        有界サンプリングを使う。ルール上のダイス分布自体は
        simulate_round_roll で完全列挙できる。
        """
        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, player_id)

        outcomes = sample_round_roll(game, samples=self.round_roll_samples)
        return expected_value(
            outcomes,
            lambda state: self._evaluate_round_roll_outcome(
                state,
                player_id,
                depth,
            ),
        )

    def _evaluate_round_roll_outcome(self, game, root_player_id, depth) -> float:
        """次ラウンドRoll後のROLL/Reroll/Actionを探索する。"""
        if depth <= 0 or getattr(getattr(game, "state", None), "game_over", False):
            return evaluate_state(game.state, root_player_id)
        current_player_id = getattr(game.state, "current_player", root_player_id)
        return self._search_node(
            game,
            root_player_id,
            current_player_id,
            depth - 1,
            float("-inf"),
            float("inf"),
        )

    def _evaluate_chance_roll(self, game, player_id, depth=None) -> float:
        """ダイスロールをChance Nodeとして展開し、各結果の期待評価値を返す。"""
        if depth is None:
            depth = self.search_depth
        if depth <= 0 or getattr(getattr(game, "state", None), "game_over", False):
            return evaluate_state(game.state, player_id)
        outcomes = simulate_roll(game, player_id)
        if not outcomes:
            return evaluate_state(game.state, player_id)
        return expected_value(
            outcomes,
            lambda outcome: self._evaluate_chance_outcome(outcome, player_id, depth),
        )

    def _evaluate_chance_outcome(self, game, player_id, depth):
        """ChanceOutcome後のGameを探索し、直接評価可能な状態にも対応する。"""
        if hasattr(game, "state"):
            current_player_id = getattr(game.state, "current_player", player_id)
            return self._search_node(
                game,
                player_id,
                current_player_id,
                depth - 1,
                float("-inf"),
                float("inf"),
            )

        if hasattr(game, "value"):
            search_node = getattr(self, "_search_node")
            if getattr(search_node, "__func__", None) is not CpuPlayer._search_node:
                return search_node(
                    game,
                    player_id,
                    player_id,
                    depth - 1,
                    float("-inf"),
                    float("inf"),
                )
            return evaluate_state(game, player_id)

        return evaluate_state(game.state, player_id)

    def _evaluate_reroll_action(self, game, root_player_id, action, depth) -> float:
        """リロールActionをChance Nodeとして展開し、結果の期待値を返す。"""
        if depth <= 0:
            return evaluate_state(game.state, root_player_id)
        outcomes = simulate_reroll(game, action)
        if not outcomes:
            return evaluate_state(game.state, root_player_id)
        return expected_value(
            outcomes,
            lambda state: self._evaluate_reroll_outcome(
                state,
                root_player_id,
                depth,
            ),
        )

    def _evaluate_reroll_outcome(self, state, root_player_id, depth) -> float:
        if hasattr(state, "state"):
            current_player_id = getattr(state.state, "current_player", root_player_id)
            return self._search_node(
                state,
                root_player_id,
                current_player_id,
                depth - 1,
                float("-inf"),
                float("inf"),
            )
        return evaluate_state(state, root_player_id)

    def _search_value(self, game, root_player_id, current_player_id, depth, alpha=float("-inf"), beta=float("inf")) -> float:
        self.last_search_nodes = 0
        return self._search_node(game, root_player_id, current_player_id, depth, alpha, beta)

    def _search_node(self, game, root_player_id, current_player_id, depth, alpha, beta) -> float:
        if self.last_search_nodes >= self.max_search_nodes:
            return evaluate_state(game.state, root_player_id)
        self.last_search_nodes += 1
        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, root_player_id)

        legal_actions = game.get_legal_actions(current_player_id)
        if not legal_actions:
            return evaluate_state(game.state, root_player_id)

        if getattr(game.state, "phase", None) is GamePhase.ROLL:
            if current_player_id == root_player_id:
                value = float("-inf")
                for action in legal_actions:
                    value = max(
                        value,
                        self._evaluate_reroll_action(game, root_player_id, action, depth),
                    )
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
                return value
            value = float("inf")
            for action in legal_actions:
                value = min(
                    value,
                    self._evaluate_reroll_action(game, root_player_id, action, depth),
                )
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

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
    def _minimax(cls, game, root_player_id, current_player_id, depth, alpha=float("-inf"), beta=float("inf")) -> float:
        if depth <= 0 or game.state.game_over:
            return evaluate_state(game.state, root_player_id)
        legal_actions = game.get_legal_actions(current_player_id)
        if not legal_actions:
            return evaluate_state(game.state, root_player_id)
        if current_player_id == root_player_id:
            value = float("-inf")
            for action in legal_actions:
                value = max(value, cls._minimax(simulate_action(game, action), root_player_id, 1 - current_player_id, depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        value = float("inf")
        for action in legal_actions:
            value = min(value, cls._minimax(simulate_action(game, action), root_player_id, 1 - current_player_id, depth - 1, alpha, beta))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def _choose_reroll(self, game, player_id, legal_actions) -> Action:
        """期待値を比較してリロールを選択する。

        全256マスクをそのまま完全展開すると分岐数が急増するため、
        従来の元素一致ヒューリスティック上位候補をChance Node評価する。
        """
        target_dice_type = self._target_dice_type(game, player_id)

        def heuristic(action):
            selected = action.target or ()
            non_matching = sum(
                1
                for dice_type in selected
                if dice_type not in (DiceType.OMNI, target_dice_type)
            )
            matching = sum(
                1 for dice_type in selected if dice_type is target_dice_type
            )
            omni = sum(
                1 for dice_type in selected if dice_type is DiceType.OMNI
            )
            return (non_matching, -matching, -omni)

        candidates = sorted(
            legal_actions,
            key=heuristic,
            reverse=True,
        )[: self.MAX_REROLL_CANDIDATES]

        return max(
            candidates,
            key=lambda action: (
                self._evaluate_reroll_action(
                    game,
                    player_id,
                    action,
                    self.search_depth,
                ),
                heuristic(action),
            ),
        )

    @staticmethod
    def _target_dice_type(game, player_id):
        element = game.state.players[player_id].active_character.element
        mapping = {
            "PYRO": DiceType.PYRO,
            "HYDRO": DiceType.HYDRO,
            "ANEMO": DiceType.ANEMO,
            "ELECTRO": DiceType.ELECTRO,
            "DENDRO": DiceType.DENDRO,
            "CRYO": DiceType.CRYO,
            "GEO": DiceType.GEO,
        }
        return mapping[element.name]

    @staticmethod
    def _best_switch_action(player, actions):
        return max(actions, key=lambda action: (
            player.characters[action.target].hp / player.characters[action.target].max_hp,
            player.characters[action.target].hp,
        ))
