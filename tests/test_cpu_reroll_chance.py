from types import SimpleNamespace

from engine.actions import Action, ActionType
from engine.dice import DiceType
from engine.state import Element
from engine.simulation import ChanceOutcome
from players.cpu import CpuPlayer


def test_cpu_chooses_reroll_by_expected_chance_value(monkeypatch):
    game = SimpleNamespace(
        state=SimpleNamespace(
            phase=__import__("engine.state", fromlist=["GamePhase"]).GamePhase.ROLL,
            players=[
                SimpleNamespace(
                    active_character=SimpleNamespace(element=Element.PYRO)
                ),
                SimpleNamespace(),
            ],
        )
    )
    keep = Action(0, ActionType.REROLL_DICE, target=())
    reroll = Action(0, ActionType.REROLL_DICE, target=(DiceType.PYRO,))
    legal_actions = [keep, reroll]
    cpu = CpuPlayer(search_depth=2)

    monkeypatch.setattr(
        "players.cpu.simulate_reroll",
        lambda _game, action: [
            ChanceOutcome(
                SimpleNamespace(value=1.0 if action is keep else 7.0),
                1.0,
            )
        ],
    )
    monkeypatch.setattr(
        "players.cpu.evaluate_state",
        lambda state, _player_id: state.value,
    )

    chosen = cpu.choose_action(game, 0, legal_actions=legal_actions)

    assert chosen is reroll
