from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from engine.cards import CardRegistry
from engine.dice import DicePool
from engine.elemental_reactions import ReactionResult, resolve_reaction
from engine.state import Element, GamePhase, GameState, PlayerState


@dataclass(frozen=True)
class Action:
    player_id: int
    action_type: "ActionType"
    target: Optional[int] = None
    card_id: Optional[str] = None


class ActionType:
    NORMAL_ATTACK = "normal_attack"
    ELEMENTAL_SKILL = "elemental_skill"
    ELEMENTAL_BURST = "elemental_burst"
    SWITCH_CHARACTER = "switch_character"
    PLAY_CARD = "play_card"
    ELEMENTAL_TUNING = "elemental_tuning"
    END_ROUND = "end_round"


class Game:
    def __init__(self, state: GameState, card_registry: Optional[CardRegistry] = None):
        self.state = state
        self.card_registry = card_registry or CardRegistry()

    def execute_action(self, action: Action) -> None:
        if self.state.game_over:
            raise ValueError("ゲーム終了後は行動できません")
        if action.player_id != self.state.current_player:
            raise ValueError("現在のプレイヤーではありません")
        if action.action_type is ActionType.NORMAL_ATTACK:
            self._require_and_pay_dice(action)
            self.normal_attack(action.player_id, action.target)
        elif action.action_type is ActionType.ELEMENTAL_SKILL:
            self._require_and_pay_dice(action)
            self.elemental_skill(action.player_id, action.target)
        elif action.action_type is ActionType.ELEMENTAL_BURST:
            self._require_and_pay_dice(action)
            self.elemental_burst(action.player_id)
            player = self.state.players[action.player_id]
            player.active_character.energy = 0
        elif action.action_type is ActionType.SWITCH_CHARACTER:
            self.switch_character(action.player_id, action.target)
        elif action.action_type is ActionType.ELEMENTAL_TUNING:
            self._execute_tuning(action)
        elif action.action_type is ActionType.END_ROUND:
            self._end_round(action.player_id)
            return
        elif action.action_type is ActionType.PLAY_CARD:
            self._execute_card(action)
        else:
            raise ValueError(f"未対応のActionTypeです: {action.action_type}")
        if not self.state.game_over:
            if action.action_type is ActionType.PLAY_CARD and self.card_registry.get(action.card_id).is_fast_action:
                return
            self._advance_turn(action.player_id)

    def _execute_card(self, action: Action) -> None:
        player = self.state.players[action.player_id]
        if action.card_id is None:
            raise ValueError("カードIDが指定されていません")
        try:
            card = self.card_registry.get(action.card_id)
        except ValueError as exc:
            raise NotImplementedError("カードが実装されていません") from exc
        if action.card_id not in player.hand:
            raise ValueError("指定されたカードが手札にありません")
        if not player.dice.can_pay(card.cost):
            raise ValueError("カードのコストを支払うダイスが不足しています")
        if not card.can_play(self, action.player_id, action.target):
            raise ValueError("現在の状態ではそのカードを使用できません")
        player.dice.pay(card.cost)
        player.hand.remove(action.card_id)
        card.play(self, action.player_id, action.target)

    def step(self, players: Sequence) -> Action:
        if self.state.game_over:
            raise ValueError("ゲーム終了後は合法手を取得できません")
        if len(players) != 2:
            raise ValueError("players must contain exactly two players")
        player_id = self.state.current_player
        legal_actions = self.get_legal_actions(player_id)
        if not legal_actions:
            raise ValueError("現在のプレイヤーに合法手がありません")
        action = players[player_id].choose_action(self, player_id, legal_actions)
        if not isinstance(action, Action):
            raise TypeError("プレイヤーはActionを返す必要があります")
        if action not in legal_actions:
            raise ValueError("プレイヤーが合法手に含まれないActionを選択しました")
        self.execute_action(action)
        return action

    # Existing game logic continues below.
