import pytest

from engine.simulation import ChanceOutcome, expected_value


class ChanceTestState:
    def __init__(self, value):
        self.value = value


def test_chance_outcome_requires_valid_probability():
    state = ChanceTestState(1)

    assert ChanceOutcome(state, 0.25).probability == 0.25
    with pytest.raises(ValueError):
        ChanceOutcome(state, -0.1)
    with pytest.raises(ValueError):
        ChanceOutcome(state, 1.1)


def test_expected_value_is_probability_weighted():
    outcomes = [
        ChanceOutcome(ChanceTestState(10), 0.25),
        ChanceOutcome(ChanceTestState(2), 0.75),
    ]

    assert expected_value(outcomes, lambda state: state.value) == pytest.approx(4.0)


def test_expected_value_requires_probabilities_to_sum_to_one():
    outcomes = [ChanceOutcome(ChanceTestState(10), 0.5)]

    with pytest.raises(ValueError):
        expected_value(outcomes, lambda state: state.value)


def test_expected_value_accepts_empty_outcomes():
    assert expected_value([], lambda state: state.value) == 0.0
