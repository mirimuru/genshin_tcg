from dataclasses import dataclass
from enum import Enum

from engine.dice import DiceType


class ActionType(Enum):
    REROLL_DICE = "reroll_dice"
    NORMAL_ATTACK = "normal_attack"
    ELEMENTAL_SKILL = "elemental_skill"
    ELEMENTAL_BURST = "elemental_burst"
    SWITCH_CHARACTER = "switch_character"
    ELEMENTAL_TUNING = "elemental_tuning"
    PLAY_CARD = "play_card"
    END_ROUND = "end_round"


@dataclass
class Action:
    player_id: int
    action_type: ActionType
    target: int | DiceType | tuple[DiceType, ...] | None = None
    card_id: str | None = None
