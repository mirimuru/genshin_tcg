"""GUIに表示するための読み取り専用状態モデル。"""

from dataclasses import dataclass

from engine.actions import Action
from engine.dice import DiceType


@dataclass(frozen=True)
class CharacterSnapshot:
    name: str
    element: str
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    aura: str | None
    statuses: tuple[str, ...]


@dataclass(frozen=True)
class PlayerSnapshot:
    player_id: int
    active_character_index: int
    characters: tuple[CharacterSnapshot, ...]
    dice: tuple[tuple[str, int], ...]
    hand: tuple[str, ...]
    combat_statuses: tuple[str, ...]
    summons: tuple[tuple[str, int], ...]
    shield: int


@dataclass(frozen=True)
class StateSnapshot:
    round_number: int
    phase: str
    current_player: int
    game_over: bool
    winner: int | None
    players: tuple[PlayerSnapshot, PlayerSnapshot]


@dataclass(frozen=True)
class ActionView:
    action: Action
    label: str
    action_type: str
    player_id: int
    target: str
    cost: str
    legal: bool


def snapshot_state(game) -> StateSnapshot:
    players = []
    for player in game.state.players:
        characters = []
        for character in player.characters:
            characters.append(
                CharacterSnapshot(
                    name=character.name,
                    element=character.element.value,
                    hp=character.hp,
                    max_hp=character.max_hp,
                    energy=character.energy,
                    max_energy=character.max_energy,
                    aura=character.elemental_aura.value if character.elemental_aura else None,
                    statuses=tuple(status.definition.name for status in character.statuses),
                )
            )
        dice = tuple((dice_type.value, player.dice.count(dice_type)) for dice_type in DiceType if dice_type not in (DiceType.ANY,))
        combat_statuses = tuple(status.definition.name for status in player.combat_statuses)
        summons = tuple((summon.definition.name, summon.usages) for summon in player.summons.values())
        players.append(
            PlayerSnapshot(
                player_id=player.player_id,
                active_character_index=player.active_character_index,
                characters=tuple(characters),
                dice=dice,
                hand=tuple(player.hand),
                combat_statuses=combat_statuses,
                summons=summons,
                shield=player.shield,
            )
        )
    return StateSnapshot(
        round_number=game.state.round_number,
        phase=game.state.phase.value,
        current_player=game.state.current_player,
        game_over=game.state.game_over,
        winner=game.state.winner,
        players=(players[0], players[1]),
    )


def _target_text(action: Action) -> str:
    if action.target is None:
        return "なし"
    if isinstance(action.target, tuple):
        return ", ".join(dice.value for dice in action.target) or "なし"
    if isinstance(action.target, DiceType):
        return action.target.value
    return f"Character {action.target + 1}"


def action_to_view(game, action: Action) -> ActionView:
    cost = game.get_action_cost(action)
    cost_text = " + ".join(
        f"{dice_type.value}×{amount}" for dice_type, amount in cost.items()
    ) or "なし"
    label = action.action_type.value
    if action.card_id:
        label = f"{label}: {action.card_id}"
    return ActionView(
        action=action,
        label=label,
        action_type=action.action_type.value,
        player_id=action.player_id,
        target=_target_text(action),
        cost=cost_text,
        legal=game.is_action_legal(action),
    )


def legal_action_views(game, player_id: int) -> tuple[ActionView, ...]:
    return tuple(action_to_view(game, action) for action in game.get_legal_actions(player_id))
