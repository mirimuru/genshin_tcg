from engine.actions import Action, ActionType


class CpuPlayer:
    """合法手一覧から行動を選択するヒューリスティックCPU。"""

    LOW_HP_THRESHOLD = 3

    def choose_action(self, game, player_id: int, legal_actions=None) -> Action:
        if legal_actions is None:
            legal_actions = game.get_legal_actions(player_id)
        if not legal_actions:
            return Action(player_id, ActionType.END_ROUND)

        def find(action_type):
            return next((action for action in legal_actions if action.action_type is action_type), None)

        switch_actions = [
            action for action in legal_actions
            if action.action_type is ActionType.SWITCH_CHARACTER
        ]
        player = game.state.players[player_id]

        if player.requires_switch and switch_actions:
            return self._best_switch_action(player, switch_actions)

        burst = find(ActionType.ELEMENTAL_BURST)
        if burst is not None:
            return burst

        if player.active_character.hp <= self.LOW_HP_THRESHOLD and switch_actions:
            return self._best_switch_action(player, switch_actions)

        skill = find(ActionType.ELEMENTAL_SKILL)
        if skill is not None:
            return skill
        attack = find(ActionType.NORMAL_ATTACK)
        if attack is not None:
            return attack
        return find(ActionType.END_ROUND) or legal_actions[0]

    @staticmethod
    def _best_switch_action(player, actions):
        return max(
            actions,
            key=lambda action: (
                player.characters[action.target].hp / player.characters[action.target].max_hp,
                player.characters[action.target].hp,
            ),
        )
