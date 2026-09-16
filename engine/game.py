from collections import Counter
from collections.abc import Sequence
import random

from engine.actions import Action, ActionType
from engine.cards import CardRegistry
from engine.dice import DicePool, DiceType
from engine.effects import create_bloom_core_generation, create_burning_flame_generation, create_catalyzing_field, create_crystallize_shield
from engine.elemental_reactions import ElementalReaction, ReactionResolver
from engine.events import DamageEvent, EffectContext, EnergyEvent, GameEvent, RoundEndEvent
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

    def deal_damage(self, attacker_id: int, target_id: int, amount: int, element: Element):
        attacker = self.state.players[attacker_id]
        target = self.state.players[target_id]
        target_character = target.active_character
        if not target_character.alive:
            return
        frozen_break_bonus = 0
        if self._is_frozen(target_character) and element in {Element.PYRO, Element.PHYSICAL}:
            target_character.remove_status("frozen")
            frozen_break_bonus = 2
        had_catalyzing_field = attacker.get_combat_status("catalyzing_field") is not None
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
        if reaction is ElementalReaction.FROZEN and not self._is_frozen(target_character):
            target_character.add_status(self._create_frozen_status())
        if reaction is ElementalReaction.BLOOM:
            attacker.add_combat_status(create_bloom_core_generation())
        if reaction is ElementalReaction.OVERLOADED and not target.defeated:
            target.must_switch = True
        if reaction is ElementalReaction.BURNING:
            attacker.add_combat_status(create_burning_flame_generation())
        if reaction is ElementalReaction.CRYSTALLIZE:
            target.add_combat_status(create_crystallize_shield())
        total_damage = amount + reaction_bonus + frozen_break_bonus
        damage_event = DamageEvent(attacker_id, target_id, total_damage, element, reaction)
        self._emit_event(damage_event)
        if reaction is ElementalReaction.QUICKEN and not had_catalyzing_field:
            attacker.add_combat_status(create_catalyzing_field(2))
        if reaction is not None:
            print(f"元素反応：{reaction.value}")
        print(f"{attacker_character_name(attacker)}が{target_character.name}に{damage_event.amount}ダメージ（{element.value}）")
        target.take_damage(damage_event.amount)
        damage_event.resolved = True
        self._emit_event(damage_event)
        if reaction in {ElementalReaction.ELECTRO_CHARGED, ElementalReaction.SUPERCONDUCT}:
            self._deal_reaction_penetration_damage(target)
        elif reaction is ElementalReaction.SWIRL and reacted_element is not None:
            self._deal_swirl_spread_damage(target, reacted_element)
        print(f"{target_character.name}のHP：{target_character.hp}/{target_character.max_hp}")
        self.state.check_game_over()

    @staticmethod
    def _create_frozen_status():
        from engine.statuses import StatusDefinition, StatusInstance
        class Frozen(StatusDefinition):
            status_id = "frozen"
            name = "凍結"
            max_usages = None
        return StatusInstance(Frozen)

    @staticmethod
    def _is_frozen(character) -> bool:
        return character.has_status("frozen")

    @staticmethod
    def _reaction_damage_bonus(reaction: ElementalReaction) -> int:
        if reaction in {ElementalReaction.VAPORIZE, ElementalReaction.MELT, ElementalReaction.OVERLOADED}:
            return 2
        if reaction in {ElementalReaction.ELECTRO_CHARGED, ElementalReaction.FROZEN, ElementalReaction.SUPERCONDUCT,
                         ElementalReaction.QUICKEN, ElementalReaction.BURNING, ElementalReaction.SWIRL,
                         ElementalReaction.CRYSTALLIZE, ElementalReaction.BLOOM}:
            return 1
        return 0

    @staticmethod
    def _deal_reaction_penetration_damage(target) -> None:
        for index, character in enumerate(target.characters):
            if index != target.active_character_index and character.alive:
                character.receive_damage(1)

    @staticmethod
    def _deal_swirl_spread_damage(target, element: Element) -> None:
        for index, character in enumerate(target.characters):
            if index != target.active_character_index and character.alive:
                character.receive_damage(1)
                character.elemental_aura = element

    def normal_attack(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは攻撃できません")
        character.definition.normal_attack(self, player_id)
        self.change_energy(player_id, self.state.players[player_id].active_character_index, 1, "normal_attack")

    def elemental_skill(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは元素スキルを使用できません")
        character.definition.elemental_skill(self, player_id)
        self.change_energy(player_id, self.state.players[player_id].active_character_index, 1, "elemental_skill")

    def elemental_burst(self, player_id: int):
        character = self.state.players[player_id].active_character
        if self._is_frozen(character):
            raise ValueError("凍結中のキャラクターは元素爆発を使用できません")
        if character.energy < character.max_energy:
            raise ValueError("元素爆発に必要なEnergyが不足しています")
        character_index = self.state.players[player_id].active_character_index
        self.change_energy(player_id, character_index, -character.max_energy, "elemental_burst")
        character.definition.elemental_burst(self, player_id)

    def get_action_cost(self, action: Action) -> dict[DiceType, int]:
        if action.action_type is ActionType.SWITCH_CHARACTER:
            return {DiceType.ANY: 1}
        if action.action_type in {ActionType.NORMAL_ATTACK, ActionType.ELEMENTAL_SKILL, ActionType.ELEMENTAL_BURST}:
            character = self.state.players[action.player_id].active_character
            return {self._element_to_dice_type(character.element): 3}
        if action.action_type is ActionType.PLAY_CARD:
            if action.card_id is None:
                return {}
            return dict(self.card_registry.get(action.card_id).cost)
        return {}

    def _card_is_legal(self, player_id: int, card_id: str, target=None) -> bool:
        player = self.state.players[player_id]
        if card_id not in player.hand:
            return False
        try:
            card = self.card_registry.get(card_id)
        except ValueError:
            return False
        return player.dice.can_pay(card.cost) and card.can_play(self, player_id, target)

    def get_legal_actions(self, player_id: int) -> list[Action]:
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
            return [Action(player_id, ActionType.SWITCH_CHARACTER, target=index) for index in player.alive_character_indices()
                    if index != player.active_character_index]
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
        for card_id in player.hand:
            action = Action(player_id, ActionType.PLAY_CARD, card_id=card_id)
            if self._card_is_legal(player_id, card_id):
                actions.append(action)
        target_dice = self._element_to_dice_type(character.element)
        actions.extend(Action(player_id, ActionType.ELEMENTAL_TUNING, target=dice_type) for dice_type in DicePool.ROLLABLE_DICE_TYPES
                       if dice_type not in (DiceType.OMNI, target_dice) and player.dice.count(dice_type) > 0)
        if player.dice.can_pay({DiceType.ANY: 1}):
            actions.extend(Action(player_id, ActionType.SWITCH_CHARACTER, target=index) for index in player.alive_character_indices()
                           if index != player.active_character_index)
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
        if player.requires_switch and action.action_type is not ActionType.SWITCH_CHARACTER:
            raise ValueError("強制交代が必要です")
        if action.action_type in {ActionType.NORMAL_ATTACK, ActionType.ELEMENTAL_SKILL, ActionType.ELEMENTAL_BURST}:
            self._require_and_pay_dice(action)
            if action.action_type is ActionType.NORMAL_ATTACK:
                self.normal_attack(player_id)
            elif action.action_type is ActionType.ELEMENTAL_SKILL:
                self.elemental_skill(player_id)
            else:
                self.elemental_burst(player_id)
            self._advance_turn(player_id)
        elif action.action_type is ActionType.SWITCH_CHARACTER:
            self._require_and_pay_dice(action)
            self._execute_switch(action)
            self._advance_turn(player_id)
        elif action.action_type is ActionType.ELEMENTAL_TUNING:
            self._execute_tuning(action)
            self._advance_turn(player_id)
        elif action.action_type is ActionType.PLAY_CARD:
            self._execute_card(action)
            self._advance_turn(player_id)
        elif action.action_type is ActionType.END_ROUND:
            self._end_round(player_id)
        else:
            raise ValueError(f"未対応のActionです: {action.action_type}")
        self.state.check_game_over()

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
        player.switch_character(action.target)
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
        mapping = {Element.PYRO: DiceType.PYRO, Element.HYDRO: DiceType.HYDRO, Element.ANEMO: DiceType.ANEMO,
                   Element.ELECTRO: DiceType.ELECTRO, Element.DENDRO: DiceType.DENDRO, Element.CRYO: DiceType.CRYO,
                   Element.GEO: DiceType.GEO}
        if element not in mapping:
            raise ValueError("物理属性のキャラクターには専用ダイスがありません")
        return mapping[element]


def attacker_character_name(player) -> str:
    return player.active_character.name
