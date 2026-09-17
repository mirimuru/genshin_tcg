from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from engine.dice import DiceType
from engine.state import Element
from engine.statuses import WeaponEquipmentStatusDefinition


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

    def get_cost(self, game, player_id: int) -> Mapping[DiceType, int]:
        """現在の状態に応じたカードコストを返す。"""
        return dict(self.cost)

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
    """武器カード。対応する武器種のキャラクターへ武器状態を装備する。"""

    equipment_slot = "weapon"
    weapon_type = ""
    VALID_WEAPON_TYPES = WeaponEquipmentStatusDefinition.VALID_WEAPON_TYPES
    WEAPON_COST_DICE = 2
    ELEMENT_TO_DICE = {
        Element.PYRO: DiceType.PYRO,
        Element.HYDRO: DiceType.HYDRO,
        Element.ANEMO: DiceType.ANEMO,
        Element.ELECTRO: DiceType.ELECTRO,
        Element.DENDRO: DiceType.DENDRO,
        Element.CRYO: DiceType.CRYO,
        Element.GEO: DiceType.GEO,
    }

    def __init__(self):
        if self.weapon_type not in self.VALID_WEAPON_TYPES:
            raise ValueError(f"weapon_typeが不正です: {self.weapon_type}")

    def get_cost(self, game, player_id: int) -> Mapping[DiceType, int]:
        element = game.state.players[player_id].active_character.definition.element
        try:
            dice_type = self.ELEMENT_TO_DICE[element]
        except KeyError as exc:
            raise ValueError("武器カードを装備できない元素です") from exc
        return {dice_type: self.WEAPON_COST_DICE}

    def can_play(self, game, player_id: int, target=None) -> bool:
        if not super().can_play(game, player_id, target):
            return False
        character = game.state.players[player_id].active_character
        return getattr(character.definition, "weapon_type", None) == self.weapon_type

    def create_status(self):
        """この武器カードが装備する状態を生成する。"""
        raise NotImplementedError

    def play(self, game, player_id: int, target=None):
        character = game.state.players[player_id].active_character
        status = self.create_status()
        if not isinstance(status, StatusInstance):
            raise TypeError("武器カードはStatusInstanceを生成する必要があります")
        if not isinstance(status.definition, WeaponEquipmentStatusDefinition):
            raise TypeError("武器カードの状態にはWeaponEquipmentStatusDefinitionが必要です")
        if status.definition.weapon_type != self.weapon_type:
            raise ValueError("武器カードと装備状態のweapon_typeが一致しません")
        character.add_equipment(status)


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
