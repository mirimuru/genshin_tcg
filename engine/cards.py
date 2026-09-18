from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from enum import Enum

from engine.dice import DiceType
from engine.state import Element
from engine.statuses import ArtifactEquipmentStatusDefinition, StatusInstance, WeaponEquipmentStatusDefinition


class CardTargetType(Enum):
    """カードが要求するTargetの種類。"""

    # 既存カードとの後方互換用。明示的なTarget制約をまだ宣言していないカード。
    UNSPECIFIED = "unspecified"
    NONE = "none"
    ACTIVE_CHARACTER = "active_character"
    ANY_ALLY_CHARACTER = "any_ally_character"


class CardDefinition(ABC):
    """カード1種類のルール定義。

    カード固有処理は ``play`` に実装し、手札には ``card_id`` の文字列を保持する。
    これによりカード追加時にゲーム本体を変更せず、カード定義を個別ファイルへ分離できる。
    """

    card_id = ""
    name = ""
    cost: Mapping[DiceType, int] = {}
    # Trueなら使用後も手番を相手へ渡さない。現段階では既定値をFalseとする。
    is_fast_action = False
    # 未指定カードは従来どおり任意のTargetを受け付ける。新規カードはTargetTypeを明示する。
    target_type = CardTargetType.UNSPECIFIED

    def get_cost(self, game, player_id: int) -> Mapping[DiceType, int]:
        """現在の状態に応じたカードコストを返す。"""
        return dict(self.cost)

    def get_legal_targets(self, game, player_id: int) -> tuple[object, ...]:
        """現在の状態で、このカードが合法手生成に使用できるTarget候補を返す。"""
        player = game.state.players[player_id]
        if self.target_type in {CardTargetType.UNSPECIFIED, CardTargetType.NONE}:
            return (None,)
        if self.target_type is CardTargetType.ACTIVE_CHARACTER:
            return (player.active_character_index,) if player.active_character.alive else ()
        if self.target_type is CardTargetType.ANY_ALLY_CHARACTER:
            return tuple(player.alive_character_indices())
        raise ValueError(f"未対応のカードTarget種別です: {self.target_type}")

    def is_target_legal(self, game, player_id: int, target=None) -> bool:
        """指定されたTargetがカードのTargetルールを満たすか判定する。"""
        if self.target_type is CardTargetType.UNSPECIFIED:
            return True
        return target in self.get_legal_targets(game, player_id)

    def can_play(self, game, player_id: int, target=None) -> bool:
        """現在の状態でカードを使用できるか判定する。"""
        return game.state.players[player_id].dice.can_pay(self.get_cost(game, player_id))

    @abstractmethod
    def play(self, game, player_id: int, target=None):
        """カード効果を適用する。"""
        raise NotImplementedError


class TalentCardDefinition(CardDefinition):
    """キャラクター固有の天賦カード。"""

    equipment_slot = "talent"
    required_character_id = ""

    def can_play(self, game, player_id: int, target=None) -> bool:
        if not super().can_play(game, player_id, target):
            return False
        if not self.required_character_id:
            return False
        return game.state.players[player_id].active_character.definition.character_id == self.required_character_id

    def create_status(self):
        """この天賦カードが装備する状態を生成する。"""
        raise NotImplementedError

    def play(self, game, player_id: int, target=None):
        character = game.state.players[player_id].active_character
        character.add_equipment(self.create_status())


class WeaponCardDefinition(CardDefinition):
    """キャラクター固有の武器種別を持つ武器カード。"""

    equipment_slot = "weapon"
    weapon_type = ""

    def get_cost(self, game, player_id: int) -> Mapping[DiceType, int]:
        """武器カードの同色コストをアクティブキャラクターの元素から解決する。"""
        character_element = game.state.players[player_id].active_character.definition.element
        dice_type = {
            Element.PYRO: DiceType.PYRO,
            Element.HYDRO: DiceType.HYDRO,
            Element.ANEMO: DiceType.ANEMO,
            Element.ELECTRO: DiceType.ELECTRO,
            Element.DENDRO: DiceType.DENDRO,
            Element.CRYO: DiceType.CRYO,
            Element.GEO: DiceType.GEO,
        }.get(character_element)
        if dice_type is None:
            raise ValueError("武器カードのコストを解決できない元素です")

        # 武器カード定義のコストをそのまま使用し、ANYコストを装備者の
        # 元素ダイスへ変換する。これにより星3通常武器の2個だけでなく、
        # 祭礼の剣のような3個コストの武器にも対応できる。
        total_cost = sum(self.cost.values())
        return {dice_type: total_cost}

    def can_play(self, game, player_id: int, target=None) -> bool:
        if not super().can_play(game, player_id, target):
            return False
        if not self.weapon_type:
            return False
        return game.state.players[player_id].active_character.definition.weapon_type == self.weapon_type

    def create_status(self) -> StatusInstance:
        """この武器カードが装備する状態を生成する。"""
        raise NotImplementedError

    def play(self, game, player_id: int, target=None):
        status = self.create_status()
        if not isinstance(status, StatusInstance) or not isinstance(status.definition, WeaponEquipmentStatusDefinition):
            raise TypeError("武器カードはWeaponEquipmentStatusDefinitionを装備する必要があります")
        if status.definition.equipment_slot != self.equipment_slot:
            raise ValueError("武器状態のequipment_slotがweaponではありません")
        if status.definition.weapon_type != self.weapon_type:
            raise ValueError("武器カードと装備状態のweapon_typeが一致しません")
        game.state.players[player_id].active_character.add_equipment(status)


class ArtifactCardDefinition(CardDefinition):
    """キャラクターに装備する聖遺物カードの共通基盤。"""

    equipment_slot = "artifact"

    def create_status(self) -> StatusInstance:
        """この聖遺物カードが装備する状態を生成する。"""
        raise NotImplementedError

    def play(self, game, player_id: int, target=None):
        status = self.create_status()
        if not isinstance(status, StatusInstance) or not isinstance(status.definition, ArtifactEquipmentStatusDefinition):
            raise TypeError("聖遺物カードはArtifactEquipmentStatusDefinitionを装備する必要があります")
        if status.definition.equipment_slot != self.equipment_slot:
            raise ValueError("聖遺物状態のequipment_slotがartifactではありません")
        game.state.players[player_id].active_character.add_equipment(status)


class CardRegistry:
    """カードIDからカード定義を解決するレジストリ。"""

    def __init__(self, definitions: Sequence[type[CardDefinition] | CardDefinition] = ()):
        self._cards: dict[str, CardDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: type[CardDefinition] | CardDefinition) -> None:
        card = definition() if isinstance(definition, type) else definition
        if not isinstance(card, CardDefinition):
            raise TypeError("カード定義はCardDefinitionまたはそのサブクラスである必要があります")
        if not card.card_id:
            raise ValueError("card_idは空にできません")
        if card.card_id in self._cards:
            raise ValueError(f"カードIDが重複しています: {card.card_id}")
        self._cards[card.card_id] = card

    def get(self, card_id: str) -> CardDefinition:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise ValueError(f"未登録のカードです: {card_id}") from exc

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __iter__(self):
        return iter(self._cards.values())
