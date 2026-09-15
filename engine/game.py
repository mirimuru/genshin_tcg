from engine.actions import Action, ActionType
from engine.state import Element


class Game:
    def __init__(self, state):
        self.state = state

    def deal_damage(self, attacker_id: int, target_id: int, amount: int, element: Element):
        attacker = self.state.players[attacker_id]
        target = self.state.players[target_id]
        target_character = target.active_character
        if not target_character.alive:
            return
        print(f"{attacker_character_name(attacker)}が{target_character.name}に{amount}ダメージ（{element.value}）")
        target_character.receive_damage(amount)
        print(f"{target_character.name}のHP：{target_character.hp}/{target_character.max_hp}")
        self.state.check_game_over()

    def normal_attack(self, player_id: int):
        character = self.state.players[player_id].active_character
        character.definition.normal_attack(self, player_id)

    def elemental_skill(self, player_id: int):
        character = self.state.players[player_id].active_character
        character.definition.elemental_skill(self, player_id)

    def elemental_burst(self, player_id: int):
        character = self.state.players[player_id].active_character
        character.definition.elemental_burst(self, player_id)

    def get_legal_actions(self, player_id: int) -> list[Action]:
        """現在の状態で player_id が実行できる行動を返す。"""
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        if self.state.game_over or player_id != self.state.current_player:
            return []

        player = self.state.players[player_id]
        if player.defeated:
            return []

        if player.requires_switch:
            return [
                Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                for index in player.alive_character_indices()
                if index != player.active_character_index
            ]

        actions = [
            Action(player_id, ActionType.NORMAL_ATTACK),
            Action(player_id, ActionType.ELEMENTAL_SKILL),
        ]
        character = player.active_character
        if character.energy >= character.max_energy:
            actions.append(Action(player_id, ActionType.ELEMENTAL_BURST))

        actions.extend(
            Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
            for index in player.alive_character_indices()
            if index != player.active_character_index
        )
        actions.append(Action(player_id, ActionType.END_ROUND))
        return actions

    def execute_action(self, action: Action) -> None:
        if not isinstance(action, Action):
            raise TypeError("action must be an Action")
        player_id = action.player_id
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        if self.state.game_over:
            raise ValueError("ゲーム終了後は行動できません")
        if player_id != self.state.current_player:
            raise ValueError("現在のプレイヤーではありません")

        player = self.state.players[player_id]
        if player.requires_switch and action.action_type is not ActionType.SWITCH_CHARACTER:
            raise ValueError("戦闘不能のため強制交代が必要です")

        if action.action_type is ActionType.SWITCH_CHARACTER:
            self._execute_switch(action)
        elif action.action_type is ActionType.NORMAL_ATTACK:
            self.normal_attack(player_id)
        elif action.action_type is ActionType.ELEMENTAL_SKILL:
            self.elemental_skill(player_id)
        elif action.action_type is ActionType.ELEMENTAL_BURST:
            self.elemental_burst(player_id)
        elif action.action_type is ActionType.END_ROUND:
            self._end_round(player_id)
            return
        elif action.action_type is ActionType.PLAY_CARD:
            raise NotImplementedError("カード処理はまだ実装されていません")
        else:
            raise ValueError(f"未対応のActionTypeです: {action.action_type}")

        if not self.state.game_over:
            self._advance_turn(player_id)

    def _execute_switch(self, action: Action) -> None:
        if action.target is None:
            raise ValueError("交代先が指定されていません")
        player = self.state.players[action.player_id]
        if not player.can_switch_to(action.target):
            raise ValueError("交代先が不正です")
        player.switch_character(action.target)

    def _advance_turn(self, player_id: int) -> None:
        self.state.current_player = 1 - player_id

    def _end_round(self, player_id: int) -> None:
        player = self.state.players[player_id]
        player.has_ended_round = True
        opponent_id = 1 - player_id
        opponent = self.state.players[opponent_id]
        if opponent.has_ended_round:
            self.state.round_number += 1
            self.state.players[0].has_ended_round = False
            self.state.players[1].has_ended_round = False
            self.state.current_player = 0
            return
        self.state.current_player = opponent_id


def attacker_character_name(player):
    return player.active_character.name
