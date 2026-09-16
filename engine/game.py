from collections import Counter
from collections.abc import Sequence
import random

from engine.actions import Action, ActionType
from engine.dice import DicePool, DiceType
from engine.elemental_reactions import ElementalReaction, ReactionResolver
from engine.state import Element, GamePhase


class Game:
    def __init__(self, state, rng: random.Random | None = None):
        self.state = state
        self.rng = rng if rng is not None else random.Random()
        self._start_roll_phase()

    def deal_damage(self, attacker_id: int, target_id: int, amount: int, element: Element):
        attacker = self.state.players[attacker_id]
        target = self.state.players[target_id]
        target_character = target.active_character
        if not target_character.alive:
            return

        frozen_break_bonus = 0
        if self._is_frozen(target_character) and element in {Element.PYRO, Element.PHYSICAL}:
            target_character.statuses.remove("frozen")
            frozen_break_bonus = 2

        had_catalyzing_field = attacker.catalyzing_field > 0
        catalyzing_field_boost = 0

        reaction = None
        reaction_bonus = 0
        reacted_element = target_character.elemental_aura
        if target_character.elemental_aura is not None:
            result = ReactionResolver.resolve(target_character.elemental_aura, element)
            reaction = result.reaction
            if reaction is not None:
                reaction_bonus = self._reaction_damage_bonus(reaction)
                target_character.elemental_aura = None
            elif element is not Element.PHYSICAL:
                target_character.elemental_aura = element
        elif element is not Element.PHYSICAL:
            target_character.elemental_aura = element

        if (
            element in {Element.DENDRO, Element.ELECTRO}
            and attacker.catalyzing_field > 0
        ):
            attacker.catalyzing_field -= 1
            if reaction is not ElementalReaction.QUICKEN:
                catalyzing_field_boost = 1

        if reaction is ElementalReaction.FROZEN and not self._is_frozen(target_character):
            target_character.statuses.append("frozen")

        dendro_core_boost = 0
        if element in {Element.PYRO, Element.ELECTRO} and attacker.dendro_core > 0:
            attacker.dendro_core -= 1
            dendro_core_boost = 2

        if reaction is ElementalReaction.BLOOM:
            attacker.dendro_core = min(2, attacker.dendro_core + 1)

        if reaction is ElementalReaction.OVERLOADED and not target.defeated:
            target.must_switch = True

        if reaction is ElementalReaction.BURNING:
            attacker.summons["burning_flame"] = min(
                2,
                attacker.summons.get("burning_flame", 0) + 1,
            )

        if reaction is ElementalReaction.QUICKEN and not had_catalyzing_field:
            attacker.catalyzing_field = 2

        total_damage = (
            amount
            + reaction_bonus
            + catalyzing_field_boost
            + dendro_core_boost
            + frozen_break_bonus
        )
        if reaction is not None:
            print(f"元素反応：{reaction.value}")
        print(
            f"{attacker_character_name(attacker)}が{target_character.name}に"
            f"{total_damage}ダメージ（{element.value}）"
        )
        target.take_damage(total_damage)

        # 結晶化のシールドは反応を起こした攻撃の後に生成される。
        if reaction is ElementalReaction.CRYSTALLIZE and target_character.alive:
            target.shield = min(2, target.shield + 1)

        if reaction in {
            ElementalReaction.ELECTRO_CHARGED,
            ElementalReaction.SUPERCONDUCT,
        }:
            self._deal_reaction_penetration_damage(target)
        elif reaction is ElementalReaction.SWIRL and reacted_element is not None:
            self._deal_swirl_spread_damage(target, reacted_element)

        print(f"{target_character.name}のHP：{target_character.hp}/{target_character.max_hp}")
        self.state.check_game_over()

    @staticmethod
    def _is_frozen(character) -> bool:
        return "frozen" in character.statuses

    @staticmethod
    def _reaction_damage_bonus(reaction: ElementalReaction) -> int:
        """元素反応による追加ダメージを返す。"""
        if reaction in {
            ElementalReaction.VAPORIZE,
            ElementalReaction.MELT,
            ElementalReaction.OVERLOADED,
        }:
            return 2

        if reaction in {
            ElementalReaction.ELECTRO_CHARGED,
            ElementalReaction.FROZEN,
            ElementalReaction.SUPERCONDUCT,
            ElementalReaction.QUICKEN,
            ElementalReaction.BURNING,
            ElementalReaction.SWIRL,
            ElementalReaction.CRYSTALLIZE,
            ElementalReaction.BLOOM,
        }:
            return 1

        return 0

    @staticmethod
    def _deal_reaction_penetration_damage(target) -> None:
        """感電・超伝導の追加1ダメージを控えキャラクターへ与える。"""
        for index, character in enumerate(target.characters):
            if index == target.active_character_index or not character.alive:
                continue
            character.receive_damage(1)

    @staticmethod
    def _deal_swirl_spread_damage(target, element: Element) -> None:
        """拡散した元素を控えキャラクターへ1ダメージとして付着させる。"""
        for index, character in enumerate(target.characters):
            if index == target.active_character_index or not character.alive:
                continue
            character.receive_damage(1)
            character.elemental_aura = element

    def normal_attack(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは攻撃できません")
        character.definition.normal_attack(self, player_id)

    def elemental_skill(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは元素スキルを使用できません")
        character.definition.elemental_skill(self, player_id)

    def elemental_burst(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは元素爆発を使用できません")
        character.definition.elemental_burst(self, player_id)

    def get_action_cost(self, action: Action) -> dict[DiceType, int]:
        """簡易ルールにおけるActionのダイスコストを返す。"""
        if action.action_type is ActionType.SWITCH_CHARACTER:
            return {DiceType.ANY: 1}

        if action.action_type in {
            ActionType.NORMAL_ATTACK,
            ActionType.ELEMENTAL_SKILL,
            ActionType.ELEMENTAL_BURST,
        }:
            character = self.state.players[action.player_id].active_character
            dice_type = self._element_to_dice_type(character.element)
            return {dice_type: 3}

        return {}

    def get_legal_actions(self, player_id: int) -> list[Action]:
        """現在の状態で player_id が実行できる行動を返す。"""
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        if self.state.game_over or player_id != self.state.current_player:
            return []

        player = self.state.players[player_id]
        if player.defeated:
            return []

        if self.state.phase is GamePhase.ROLL:
            if player.has_rerolled:
                return []
            return self._get_reroll_actions(player_id)

        if player.requires_switch:
            return [
                Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                for index in player.alive_character_indices()
                if index != player.active_character_index
            ]

        actions = []
        character = player.active_character
        if not self._is_frozen(character):
            normal_attack = Action(player_id, ActionType.NORMAL_ATTACK)
            skill = Action(player_id, ActionType.ELEMENTAL_SKILL)
            if player.dice.can_pay(self.get_action_cost(normal_attack)):
                actions.append(normal_attack)
            if player.dice.can_pay(self.get_action_cost(skill)):
                actions.append(skill)

            if character.energy >= character.max_energy:
                burst = Action(player_id, ActionType.ELEMENTAL_BURST)
                if player.dice.can_pay(self.get_action_cost(burst)):
                    actions.append(burst)

        target_dice = self._element_to_dice_type(character.element)
        actions.extend(
            Action(player_id, ActionType.ELEMENTAL_TUNING, target=dice_type)
            for dice_type in DicePool.ROLLABLE_DICE_TYPES
            if dice_type not in (DiceType.OMNI, target_dice)
            and player.dice.count(dice_type) > 0
        )

        if player.dice.can_pay({DiceType.ANY: 1}):
            actions.extend(
                Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                for index in player.alive_character_indices()
                if index != player.active_character_index
            )
        actions.append(Action(player_id, ActionType.END_ROUND))
        return actions

    def execute_action(self, action: Action) -> None:
        if not isinstance(action, Action):
            raise TypeError("action must be Action")
        player_id = action.player_id
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        if self.state.game_over:
            raise ValueError("ゲーム終了後は行動できません")
        if player_id != self.state.current_player:
            raise ValueError("現在のプレイヤーではありません")

        player = self.state.players[player_id]
        if self.state.phase is GamePhase.ROLL:
            if action.action_type is not ActionType.REROLL_DICE:
                raise ValueError("ロールフェーズではリロールのみ実行できます")
            self._execute_reroll(action)
            return

        if action.action_type is ActionType.REROLL_DICE:
            raise ValueError("アクションフェーズではリロールできません")

        if player.requires_switch and action.action_type is not ActionType.SWITCH_CHARACTER:
            raise ValueError("戦闘不能のため強制交代が必要です")

        if self._is_frozen(player.active_character) and action.action_type in {
            ActionType.NORMAL_ATTACK,
            ActionType.ELEMENTAL_SKILL,
            ActionType.ELEMENTAL_BURST,
        }:
            raise ValueError("凍結中のキャラクターはこの行動を実行できません")

        if action.action_type is ActionType.SWITCH_CHARACTER:
            was_forced_switch = player.requires_switch
            if not was_forced_switch and not player.dice.can_pay(self.get_action_cost(action)):
                raise ValueError("ダイスが不足しています")
            self._execute_switch(action)
            if not was_forced_switch:
                player.dice.pay(self.get_action_cost(action))
        elif action.action_type is ActionType.ELEMENTAL_TUNING:
            self._execute_tuning(action)
            return
        elif action.action_type is ActionType.NORMAL_ATTACK:
            self._require_and_pay_dice(action)
            self.normal_attack(player_id)
        elif action.action_type is ActionType.ELEMENTAL_SKILL:
            self._require_and_pay_dice(action)
            self.elemental_skill(player_id)
        elif action.action_type is ActionType.ELEMENTAL_BURST:
            self._require_and_pay_dice(action)
            self.elemental_burst(player_id)
            player.active_character.energy = 0
        elif action.action_type is ActionType.END_ROUND:
            self._end_round(player_id)
            return
        elif action.action_type is ActionType.PLAY_CARD:
            raise NotImplementedError("カード処理はまだ実装されていません")
        else:
            raise ValueError(f"未対応のActionTypeです: {action.action_type}")

        if not self.state.game_over:
            self._advance_turn(player_id)

    def step(self, players: Sequence) -> Action:
        """現在の手番プレイヤーに1回だけ行動させ、実行したActionを返す。"""
        if self.state.game_over:
            raise ValueError("ゲーム終了後は合法手を取得できません")
        if len(players) != 2:
            raise ValueError("players must contain exactly two players")

        player_id = self.state.current_player
        legal_actions = self.get_legal_actions(player_id)
        if not legal_actions:
            raise ValueError("現在のプレイヤーに合法手がありません")

        player = players[player_id]
        action = player.choose_action(self, player_id, legal_actions)
        if not isinstance(action, Action):
            raise TypeError("プレイヤーはActionを返す必要があります")
        if action not in legal_actions:
            raise ValueError("プレイヤーが合法手に含まれないActionを選択しました")

        self.execute_action(action)
        self.state.check_game_over()
        return action

    def run(self, players: Sequence, max_actions: int = 1000) -> list[Action]:
        """ゲーム終了または最大行動数到達まで自動対戦を実行する。"""
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
        actions = []
        for mask in range(1 << len(dice)):
            selected = tuple(dice[index] for index in range(len(dice)) if mask & (1 << index))
            actions.append(Action(player_id, ActionType.REROLL_DICE, target=selected))
        return actions

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
        player.switch_character(action.target)
        if player.must_switch:
            player.must_switch = False

    def _require_and_pay_dice(self, action: Action) -> None:
        cost = self.get_action_cost(action)
        player = self.state.players[action.player_id]
        if not player.dice.can_pay(cost):
            raise ValueError("ダイスが不足しています")
        player.dice.pay(cost)

    @staticmethod
    def _element_to_dice_type(element: Element) -> DiceType:
        mapping = {
            Element.PYRO: DiceType.PYRO,
            Element.HYDRO: DiceType.HYDRO,
            Element.ANEMO: DiceType.ANEMO,
            Element.ELECTRO: DiceType.ELECTRO,
            Element.DENDRO: DiceType.DENDRO,
            Element.CRYO: DiceType.CRYO,
            Element.GEO: DiceType.GEO,
        }
        if element not in mapping:
            return DiceType.OMNI
        return mapping[element]

    def _advance_turn(self, player_id: int) -> None:
        self.state.current_player = 1 - player_id

    def _end_round(self, player_id: int) -> None:
        player = self.state.players[player_id]
        player.has_ended_round = True

        if not all(other.has_ended_round for other in self.state.players):
            self._advance_turn(player_id)
            return

        self._resolve_end_phase()
        self.state.round_number += 1
        self.state.phase = GamePhase.ROLL
        for other in self.state.players:
            other.has_ended_round = False
            other.has_rerolled = False
        self._start_roll_phase()

    def _resolve_end_phase(self) -> None:
        for player in self.state.players:
            usages = player.summons.get("burning_flame", 0)
            if usages > 0:
                target = self.state.opponent_of(player.player_id)
                target.active_character.receive_damage(1)
                if usages <= 1:
                    player.summons.pop("burning_flame", None)
                else:
                    player.summons["burning_flame"] = usages - 1
            self.state.check_game_over()


def attacker_character_name(player) -> str:
    return player.active_character.name
