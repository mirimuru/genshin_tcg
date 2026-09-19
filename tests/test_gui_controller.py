from engine.actions import ActionType
from gui.game_view import GuiController, default_game_factory


def test_controller_creates_game_and_state_snapshot():
    controller = GuiController(default_game_factory)
    assert controller.state_snapshot.round_number == 1
    assert controller.state_snapshot.phase == "roll"
    assert controller.state_snapshot.current_player == 0
    assert len(controller.state_snapshot.players) == 2
    assert len(controller.state_snapshot.players[0].characters) == 3
    assert controller.action_views


def test_controller_exposes_legal_actions_with_cost_and_target():
    controller = GuiController(default_game_factory)
    views = controller.action_views
    assert all(view.legal for view in views)
    assert all(view.cost for view in views)
    assert any(view.action.action_type is ActionType.REROLL_DICE for view in views)


def test_controller_executes_existing_action_path_and_refreshes():
    controller = GuiController(default_game_factory)
    action = next(view.action for view in controller.action_views if not view.action.target)
    assert controller.execute_action(action)
    assert controller.state_snapshot.players[0].dice
    assert controller.current_player_id == 1


def test_controller_reports_illegal_action_without_changing_state():
    controller = GuiController(default_game_factory)
    before = controller.state_snapshot
    from engine.actions import Action

    illegal = Action(1, ActionType.NORMAL_ATTACK)
    assert not controller.execute_action(illegal)
    assert controller.state_snapshot == before
    assert controller.last_error
