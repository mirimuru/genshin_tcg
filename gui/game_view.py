"""GUIと既存Game APIを接続するController。"""

import random
from typing import Callable

from engine.game import Game
from engine.state import GameState, PlayerState
from gui.debug_state import ActionView, StateSnapshot, action_to_view, legal_action_views, snapshot_state
from gui.event_log import EventLog


class DebugGame(Game):
    """イベントをGUIログへ転送するGame薄型ラッパー。

    ルール処理はすべて親クラスへ委譲し、GUI固有のイベント収集だけを追加する。
    """

    def __init__(self, state, event_log: EventLog, rng=None, card_registry=None):
        self._debug_event_log = event_log
        super().__init__(state, rng=rng, card_registry=card_registry)

    def _emit_event(self, event):
        self._debug_event_log.record(event)
        super()._emit_event(event)


class GuiController:
    """Gameを直接編集せず、GUI操作を既存Action経路へ渡す。"""

    def __init__(self, game_factory: Callable[[], Game]):
        self.game_factory = game_factory
        self.event_log = EventLog()
        self.game = game_factory()
        self.current_player_id = self.game.state.current_player
        self.state_snapshot: StateSnapshot = snapshot_state(self.game)
        self.action_views: tuple[ActionView, ...] = ()
        self.last_error: str | None = None
        self.refresh()

    def refresh(self) -> None:
        self.current_player_id = self.game.state.current_player
        self.state_snapshot = snapshot_state(self.game)
        if self.game.state.game_over:
            self.action_views = ()
        else:
            self.action_views = legal_action_views(self.game, self.current_player_id)

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
        self.event_log.clear()
        self.game = self.game_factory()
        self.last_error = None
        self.refresh()

    def get_action_view(self, index: int) -> ActionView:
        return self.action_views[index]


def create_default_game() -> DebugGame:
    """手動検証用の固定チームでゲームを開始する。"""
    from content.characters import DILUC, KAEYA, XINGQIU

    players = [
        PlayerState(0, [DILUC.create_state(), KAEYA.create_state(), XINGQIU.create_state()]),
        PlayerState(1, [XINGQIU.create_state(), DILUC.create_state(), KAEYA.create_state()]),
    ]
    return DebugGame(
        GameState(players),
        event_log=_DEFAULT_EVENT_LOG,
        rng=random.Random(0),
    )


_DEFAULT_EVENT_LOG = EventLog()


def default_game_factory() -> DebugGame:
    """Controller用の新しいGameを作るFactory。"""
    from content.characters import DILUC, KAEYA, XINGQIU

    log = EventLog()
    players = [
        PlayerState(0, [DILUC.create_state(), KAEYA.create_state(), XINGQIU.create_state()]),
        PlayerState(1, [XINGQIU.create_state(), DILUC.create_state(), KAEYA.create_state()]),
    ]
    return DebugGame(GameState(players), event_log=log, rng=random.Random(0))
