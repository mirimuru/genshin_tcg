from engine.dice import DicePool, DiceType


def test_roll_outcomes_are_discrete_and_sum_to_one():
    outcomes = DicePool.roll_outcomes(1, [DiceType.OMNI, DiceType.PYRO])

    assert sum(probability for _, probability in outcomes) == 1.0
    assert len(outcomes) == 2
    assert all(len(pool) == 1 for pool, _ in outcomes)


def test_roll_outcomes_are_not_affected_by_rng_state():
    first = DicePool.roll_outcomes(2, [DiceType.OMNI, DiceType.PYRO])
    second = DicePool.roll_outcomes(2, [DiceType.OMNI, DiceType.PYRO])

    assert first == second


def test_roll_outcomes_uses_uniform_distribution_for_two_faces():
    outcomes = DicePool.roll_outcomes(1, [DiceType.OMNI, DiceType.PYRO])

    assert {(pool.count(DiceType.OMNI), pool.count(DiceType.PYRO), probability) for pool, probability in outcomes} == {
        (1, 0, 0.5),
        (0, 1, 0.5),
    }
