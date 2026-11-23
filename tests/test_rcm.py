import numpy as np
import pytest

from stat605.rcm import rcm

RULES = ("kin", "mmd-r", "mmd-dr")


@pytest.mark.parametrize("rule", RULES)
def test_first_two_steps(rule):
    states = list(rcm(lambda x: x, [1], 0.5, 2, rule))
    np.testing.assert_array_equal([s.x[0] for s in states], [1, 0.75, 0.3125])
    np.testing.assert_array_equal([s.v[0] for s in states], [0, -0.5, -0.875])
    assert not any(s.restarted for s in states)
    assert states[-1].gradient_calls == 3


@pytest.mark.parametrize("rule,first_restart", [("kin", 4), ("mmd-r", 3), ("mmd-dr", 3)])
def test_restart_endpoint_and_clock(rule, first_restart):
    states = list(rcm(lambda x: x, [1], 0.5, first_restart + 1, rule))
    assert next(s.iteration for s in states if s.restarted) == first_restart
    before, after = states[first_restart - 1 : first_restart + 1]
    np.testing.assert_array_equal(after.v, -0.5 * before.x)
    np.testing.assert_array_equal(after.x, 0.75 * before.x)
    assert after.segment_steps == 1
    assert states[-1].segment_steps == 2
    assert after.gradient_calls == first_restart + 1 + (rule == "mmd-dr")


@pytest.mark.parametrize("rule", RULES)
def test_equality_and_iteration_cap(rule):
    states = list(rcm(lambda x: x, [0], 0.5, 4, rule))
    assert [s.iteration for s in states] == list(range(5))
    assert not any(s.restarted for s in states)


@pytest.mark.parametrize("rule", RULES)
def test_nonfinite_gradient(rule):
    def gradient(x):
        return x if x[0] >= 0.5 else np.array([np.nan])

    with pytest.raises(FloatingPointError):
        list(rcm(gradient, [1], 0.5, 2, rule))
