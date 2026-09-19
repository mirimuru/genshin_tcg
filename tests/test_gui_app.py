from gui.game_view import GuiController, default_game_factory
from gui.app import DebugApp


def test_state_text_contains_core_debug_fields():
    controller = GuiController(default_game_factory)
    text = DebugApp._state_text(controller.state_snapshot)
    assert "STATE INSPECTOR" in text
    assert "Round: 1" in text
    assert "Phase: roll" in text
    assert "Current Player: P1" in text
    assert "HP 10/10" in text
    assert "Energy 0/" in text


def test_app_module_exposes_main_entrypoint():
    from gui import app

    assert callable(app.main)
