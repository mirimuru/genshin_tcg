from gui.event_log import EventLog
from gui.game_view import GuiController, default_game_factory


def test_event_log_formats_action_event():
    controller = GuiController(default_game_factory)
    action = next(view.action for view in controller.action_views if view.action.target == ())
    assert controller.execute_action(action)
    assert controller.event_log.entries == []


def test_event_log_records_events_after_action_phase():
    controller = GuiController(default_game_factory)
    for _ in range(2):
        action = next(view.action for view in controller.action_views if view.action.target == ())
        assert controller.execute_action(action)

    end_round = next(view.action for view in controller.action_views if view.action.action_type.value == "end_round")
    assert controller.execute_action(end_round)
    assert controller.event_log.entries
    assert any("Round End" in entry for entry in controller.event_log.entries)


def test_event_log_clear_is_independent_between_games():
    controller = GuiController(default_game_factory)
    controller.event_log.entries.append("test")
    controller.new_game()
    assert controller.event_log.entries == []
