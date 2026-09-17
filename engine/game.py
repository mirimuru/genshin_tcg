from collections import Counter
from collections.abc import Sequence
import random

from engine.actions import Action, ActionType
from engine.cards import CardRegistry
from engine.dice import DicePool, DiceType
from engine.effects import create_bloom_core_generation, create_burning_flame_generation, create_catalyzing_field, create_crystallize_shield
from engine.elemental_reactions import ElementalReaction, ReactionResolver
from engine.events import (
    CardActionEvent,
    CharacterSwitchEvent,
    DamageEvent,
    EffectContext,
    ElementalBurstEvent,
    ElementalSkillEvent,
    EnergyEvent,
    GameEvent,
    NormalAttackEvent,
    RoundEndEvent,
)
from engine.state import Element, GamePhase


class Game:
    def __init__(self, state, rng: random.Random | None = None, card_registry: CardRegistry | None = None):
        self.state = state
        self.rng = rng if rng is not None else random.Random()
        self.card_registry = card_registry if card_registry is not None else CardRegistry()
        self._start_roll_phase()

    def _emit_event(self, event: GameEvent) -> None:
        """現在存在するStatus/Summonへイベントを通知する。"""
        for player in self.state.players:
            combat_statuses = list(player.combat_statuses)
            summons = list(player.summons.values())
            character_statuses = [(index, status) for index, character in enumerate(player.characters) for status in list(character.statuses)]
            for status in combat_statuses:
                status.definition.on_event(status, event, self, EffectContext(player.player_id))
            for summon in summons:
                summon.definition.on_event(summon, event, self, EffectContext(player.player_id))
            for index, status in character_statuses:
                status.definition.on_event(status, event, self, EffectContext(player.player_id, index))
            player.remove_expired_combat_statuses()
            player.remove_expired_summons()
            for character in player.characters:
                character.remove_expired_statuses()

    def _modify_damage_input(self, attacker_id: int, amount: int, element: Element):
        """攻撃者のCharacter Statusでダメージ量・元素を確定前に変更する。"""
        character = self.state.players[attacker_id].active_character
        for status in list(character.statuses):
            amount, element = status.definition.modify_damage(
                status,
                amount,
                element,
                self,
                EffectContext(attacker_id, self.state.players[attacker_id].active_character_index),
            )
        character.remove_expired_statuses()
        return amount, element

    def change_energy(self, player_id: int, character_index: int, amount: int, reason: str) -> int:
        """Energyの増減をイベントとして解決し、実際に変化した値を返す。"""
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        player = self.state.players[player_id]
        if not 0 <= character_index < len(player.characters):
            raise ValueError("character_indexが不正です")
        if not isinstance(amount, int):
            raise TypeError("energy amount must be an integer")
        if amount < 0:
            character = player.characters[character_index]
            if character.energy + amount < 0:
                raise ValueError("Energyが不足しています")
        event = EnergyEvent(player_id, character_index, amount, reason)
        self._emit_event(event)
        character = player.characters[character_index]
        old_energy = character.energy
        character.energy = max(0, min(character.max_energy, character.energy + event.amount))
        event.amount = character.energy - old_energy
        event.resolved = True
        self._emit_event(event)
        return event.amount

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
        event = CardActionEvent(action.player_id, action.card_id, action.target)
        self._emit_event(event)
        card.play(self, action.player_id, action.target)
        event.resolved = True
        self._emit_event(event)

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
        self.state.check_game_over()
        return action

    def run(self, players: Sequence, max_actions: int = 1000) -> list[Action]:
        if len(players) != 2:
            raise ValueError("players must contain exactly two players")
        if max_actions < 1:
            raise ValueError("max_actions must be positive")
        actions = []
        while not self.state.game_over and len(actions) < max_actions:
            actions.append(self.step(players))
        return actions

    def _get_reroll_actions(self, player_id: int) -> list[Action]:
        dice = self.state.players[player_id].dice.as_list()
        return [Action(player_id, ActionType.REROLL_DICE, target=tuple(dice[index] for index in range(len(dice)) if mask & (1 << index))) for mask in range(1 << len(dice))]

    def _execute_reroll(self, action: Action) -> None:
        player = self.state.players[action.player_id]
        if player.has_rerolled:
            raise ValueError("このラウンドではすでにリロール済みです")
        if not isinstance(action.target, tuple):
            raise ValueError("リロール対象のダイスがタプルで指定されていません")
        if any(not isinstance(dice_type, DiceType) or dice_type is DiceType.ANY for dice_type in action.target):
            raise ValueError("リロール対象が不正です")
        player.dice.reroll(Counter(action.target), self.rng)
        player.has_rerolled = True
        opponent_id = 1 - action.player_id
        opponent = self.state.players[opponent_id]
        if opponent.has_rerolled:
            self.state.phase = GamePhase.ACTION
            self.state.current_player = 0
        else:
            self.state.current_player = opponent_id

    def _start_roll_phase(self) -> None:
        self.state.phase = GamePhase.ROLL
        self.state.current_player = 0
        for player in self.state.players:
            player.dice = DicePool.roll(self.rng)
            player.has_rerolled = False

    def _execute_switch(self, action: Action) -> None:
        if action.target is None:
            raise ValueError("交代先が指定されていません")
        player = self.state.players[action.player_id]
        if not isinstance(action.target, int) or not player.can_switch_to(action.target):
            raise ValueError("交代先が不正です")
        from_index = player.active_character_index
        event = CharacterSwitchEvent(action.player_id, from_index, action.target)
        self._emit_event(event)
        player.switch_character(action.target)
        event.resolved = True
        self._emit_event(event)
        if player.must_switch:
            player.must_switch = False

    def _require_and_pay_dice(self, action: Action) -> None:
        cost = self.get_action_cost(action)
        player = self.state.players[action.player_id]
        if not player.dice.can_pay(cost):
            raise ValueError("ダイスが不足しています")
        player.dice.pay(cost)

    def _execute_tuning(self, action: Action) -> None:
        player = self.state.players[action.player_id]
        if not isinstance(action.target, DiceType) or action.target is DiceType.ANY:
            raise ValueError("変換先のダイス種別が不正です")
        if action.target not in DicePool.ROLLABLE_DICE_TYPES:
            raise ValueError("変換先に選択できないダイスです")
        active_dice_type = self._element_to_dice_type(player.active_character.element)
        if action.target is active_dice_type or action.target is DiceType.OMNI:
            raise ValueError("変換先が不正です")
        if player.dice.count(action.target) <= 0:
            raise ValueError("変換元のダイスが不足しています")
        player.dice.harmonize(action.target, active_dice_type)

    def _end_round(self, player_id: int) -> None:
        player = self.state.players[player_id]
        player.has_ended_round = True
        opponent = self.state.players[1 - player_id]
        if opponent.has_ended_round:
            self._resolve_end_of_round_effects()
            if not self.state.game_over:
                self._start_next_round()
        else:
            self.state.current_player = 1 - player_id

    def _resolve_end_of_round_effects(self) -> None:
        for player_id in range(2):
            self._emit_event(RoundEndEvent(player_id))
            if self.state.game_over:
                break
        for player in self.state.players:
            for character in player.characters:
                character.remove_status("frozen")
            player.remove_expired_combat_statuses()
            player.remove_expired_summons()

    def _start_next_round(self) -> None:
        self.state.round_number += 1
        self.state.phase = GamePhase.ROLL
        self.state.current_player = 0
        for player in self.state.players:
            player.has_ended_round = False
            player.has_rerolled = False
            player.dice = DicePool.roll(self.rng)

    def _advance_turn(self, player_id: int):
        self.state.current_player = 1 - player_id

    @staticmethod
    def _element_to_dice_type(element: Element) -> DiceType:
        mapping = {Element.PYRO: DiceType.PYRO, Element.HYDRO: DiceType.HYDRO, Element.ANEMO: DiceType.ANEMO, Element.ELECTRO: DiceType.ELECTRO, Element.DENDRO: DiceType.DENDRO, Element.CRYO: DiceType.CRYO, Element.GEO: DiceType.GEO}
        if element not in mapping:
            raise ValueError("物理属性のキャラクターには専用ダイスがありません")
        return mapping[element]


def attacker_character_name(player) -> str:
    return player.active_character.name
