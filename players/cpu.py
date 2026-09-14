from engine.actions import Action, ActionType


class CpuPlayer:
    """現在のゲーム状態から単一の行動を選択するCPUプレイヤー。

    現段階では、ゲームエンジン側のダイス消費やカード処理が未実装でも
    動作できるよう、状態だけから判断できるヒューリスティックを使用する。
    """

    LOW_HP_THRESHOLD = 3

    def choose_action(self, game, player_id: int) -> Action:
        """現在の状態からCPUが実行したい行動を返す。"""
        player = game.state.players[player_id]

        # アクティブキャラクターが倒れている場合は、まず強制交代を行う。
        if player.requires_switch:
            return Action(
                player_id=player_id,
                action_type=ActionType.SWITCH_CHARACTER,
                target=self._best_switch_target(player),
            )

        # 全員戦闘不能ならゲーム終了済みなので行動は不要。
        if player.defeated:
            return Action(player_id=player_id, action_type=ActionType.END_ROUND)

        # 元素爆発を使用できるなら最優先する。
        character = player.active_character
        if character.energy >= character.max_energy:
            return Action(
                player_id=player_id,
                action_type=ActionType.ELEMENTAL_BURST,
            )

        # HPが危険域なら、残っているキャラクターへ交代する。
        if character.hp <= self.LOW_HP_THRESHOLD:
            target = self._best_switch_target(player)
            if target is not None:
                return Action(
                    player_id=player_id,
                    action_type=ActionType.SWITCH_CHARACTER,
                    target=target,
                )

        # 次点として元素スキルを選択する。
        return Action(
            player_id=player_id,
            action_type=ActionType.ELEMENTAL_SKILL,
        )

    @staticmethod
    def _best_switch_target(player):
        """交代先として最もHP割合の高い生存キャラクターを選ぶ。"""
        candidates = [
            index
            for index in player.alive_character_indices()
            if index != player.active_character_index
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda index: (
                player.characters[index].hp / player.characters[index].max_hp,
                player.characters[index].hp,
            ),
        )
