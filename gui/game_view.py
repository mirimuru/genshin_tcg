"""GUIと既存Game APIを接続するController。"""

import random
from typing import Callable

from engine.events import RoundEndEvent
from engine.game import Game
from engine.state import GameState, PlayerState
from gui.debug_state import ActionView, StateSnapshot, legal_action_views, snapshot_state
from gui.event_log import EventLog


class DebugGame(Game):
    """イベントをGUIログへ転送するGame薄型ラッパー。"""

    def __init__(self, state, event_log: EventLog, rng=None, card_registry=None):
        self._debug_event_log = event_log
        super().__init__(state, rng=rng, card_registry=card_registry)

    def _emit_event(self, event):
        self._debug_event_log.record(event)
        super()._emit_event(event)

    def _end_round(self, player_id: int) -> None:
        """GUIではラウンド終了宣言も追跡できるようにする。

        通常のGameではRoundEndEventは両プレイヤーが終了を宣言した後の
        解決時にだけ発行される。そのためGUIで最初のEND_ROUND操作を
        行った時点でも人間が操作履歴を追えるよう、まだ相手が終了して
        いない場合だけログへ記録する。実際の解決時のイベントは
        Game._resolve_end_of_round_effects() が従来どおり発行する。
        """
        opponent = self.state.players[1 - player_id]
        if not opponent.has_ended_round:
            self._debug_event_log.record(RoundEndEvent(player_id))
        super()._end_round(player_id)


class GuiController:
    """Gameを直接編集せず、GUI操作を既存Action経路へ渡す。"""

    def __init__(self, game_factory: Callable[[], Game]):
        self.game_factory = game_factory
        self.game = game_factory()
        self.event_log = getattr(self.game, "_debug_event_log", EventLog())
        self.current_player_id = self.game.state.current_player
        self.state_snapshot: StateSnapshot = snapshot_state(self.game)
        self.action_views: tuple[ActionView, ...] = ()
        self.last_error: str | None = None
        self.refresh()

    def refresh(self) -> None:
        self.current_player_id = self.game.state.current_player
        self.state_snapshot = snapshot_state(self.game)
        self.action_views = () if self.game.state.game_over else legal_action_views(self.game, self.current_player_id)

    def execute_action(self, action) -> bool:
        self.last_error = None
        try:
            self.game.execute_action(action)
        except (TypeError, ValueError, NotImplementedError) as exc:
            self.last_error = str(exc)
            self.refresh()
            return False
        self.refresh()
        return True

    def new_game(self) -> None:
        self.game = self.game_factory()
        self.event_log = getattr(self.game, "_debug_event_log", EventLog())
        self.last_error = None
        self.refresh()

    def get_action_view(self, index: int) -> ActionView:
        return self.action_views[index]


def default_game_factory() -> DebugGame:
    """手動検証用の固定チームで新しいゲームを作る。"""
    from content.characters import DILUC, KAEYA, XINGQIU

    log = EventLog()
    players = [
        PlayerState(0, [DILUC.create_state(), KAEYA.create_state(), XINGQIU.create_state()]),
        PlayerState(1, [XINGQIU.create_state(), DILUC.create_state(), KAEYA.create_state()]),
    ]
    return DebugGame(GameState(players), event_log=log, rng=random.Random(0))
