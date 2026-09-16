from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from engine.dice import DiceType


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

    def can_play(self, game, player_id: int, target=None) -> bool:
        """現在の状態でカードを使用できるか判定する。"""
        return game.state.players[player_id].dice.can_pay(self.cost)

    @abstractmethod
    def play(self, game, player_id: int, target=None):
        """カード効果を適用する。"""
        raise NotImplementedError


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
