from enum import Enum
from typing import List, Optional

from engine.dice import DicePool


class Element(Enum):
    PYRO = "炎"
    HYDRO = "水"
    ANEMO = "風"
    ELECTRO = "雷"
    DENDRO = "草"
    CRYO = "氷"
    GEO = "岩"
    PHYSICAL = "物理"


class GamePhase(Enum):
    ROLL = "roll"
    ACTION = "action"


class CharacterState:
    def __init__(
        self,
        name: str,
        element: Element,
        max_hp: int = 10,
        max_energy: int = 2,
    ):
        if max_hp <= 0:
            raise ValueError("max_hp must be greater than 0")
        if max_energy < 0:
            raise ValueError("max_energy must not be negative")

        self.name = name
        self.element = element

        self.max_hp = max_hp
        self.hp = max_hp

        self.max_energy = max_energy
        self.energy = 0

        self.elemental_aura: Optional[Element] = None
        self.statuses = []

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def defeated(self) -> bool:
        return not self.alive

    def receive_damage(self, amount: int) -> int:
        """ダメージを受け、実際に減少したHPを返す。"""
        if amount < 0:
            raise ValueError("damage amount must not be negative")

        old_hp = self.hp
        self.hp = max(0, self.hp - amount)
        return old_hp - self.hp

    def heal(self, amount: int) -> int:
        """回復し、実際に増加したHPを返す。"""
        if amount < 0:
            raise ValueError("heal amount must not be negative")

        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp


class PlayerState:
    def __init__(self, player_id: int, characters: List[CharacterState]):
        if len(characters) != 3:
            raise ValueError("七聖召喚ではキャラクターを3体指定してください")

        self.player_id = player_id
        self.characters = characters
        self.active_character_index = 0

        self.dice = DicePool.default()
        self.hand = []
        self.deck = []
        self.summons = {}

        self.has_ended_round = False
        self.has_rerolled = False
        self.must_switch = False
        self.dendro_core = 0
        # 原激化フィールド。次の草・雷ダメージ2回をそれぞれ1増加させる。
        self.catalyzing_field = 0

    @property
    def active_character(self) -> CharacterState:
        return self.characters[self.active_character_index]

    @property
    def defeated(self) -> bool:
        return all(not character.alive for character in self.characters)

    @property
    def requires_switch(self) -> bool:
        """強制交代が必要か判定する。"""
        return (self.must_switch or not self.active_character.alive) and not self.defeated

    def can_switch_to(self, index: int) -> bool:
        """指定したキャラクターへ交代可能か判定する。"""
        if not 0 <= index < len(self.characters):
            return False

        if index == self.active_character_index:
            return False

        if not self.characters[index].alive:
            return False

        return True

    def switch_character(self, index: int) -> None:
        """指定したキャラクターへ交代する。"""
        if not 0 <= index < len(self.characters):
            raise ValueError("存在しないキャラクター番号です")

        if index == self.active_character_index:
            raise ValueError("すでにアクティブなキャラクターです")

        if not self.characters[index].alive:
            raise ValueError("戦闘不能のキャラクターには交代できません")

        self.active_character_index = index

    def alive_character_indices(self) -> List[int]:
        """生存しているキャラクターのインデックスを返す。"""
        return [
            index
            for index, character in enumerate(self.characters)
            if character.alive
        ]


class GameState:
    def __init__(self, players: List[PlayerState]):
        if len(players) != 2:
            raise ValueError("プレイヤーは2人必要です")

        self.players = players
        self.round_number = 1
        self.phase = GamePhase.ROLL
        self.current_player = 0
        self.game_over = False
        self.winner: Optional[int] = None

        self.check_game_over()

    def opponent_of(self, player_id: int) -> PlayerState:
        if player_id not in (0, 1):
            raise ValueError("player_id must be 0 or 1")
        return self.players[1 - player_id]

    def check_game_over(self) -> bool:
        """
        どちらかのプレイヤーの3キャラクター全員が戦闘不能ならゲーム終了。
        ゲーム終了ならwinnerも設定する。
        """
        defeated_players = [
            player.player_id for player in self.players if player.defeated
        ]

        self.game_over = bool(defeated_players)

        if len(defeated_players) == 1:
            self.winner = 1 - defeated_players[0]
        elif len(defeated_players) == 2:
            self.winner = None
        else:
            self.winner = None

        return self.game_over
