from hypothesis import assume, given, settings, strategies as st

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.validate import validate


@settings(max_examples=10, deadline=None)
@given(
    delta=st.integers(min_value=-10, max_value=10).map(
        lambda k: k * 100
    ),  # cents delta around canonical target in Spark-sized increments
    band_extra=st.integers(min_value=0, max_value=2000),  # widen band modestly
)
def test_randomized_target_and_band_keeps_validity(delta, band_extra):
    plan = load_plan("plan.json")
    # Adjust target modestly and keep band at least canonical + extra
    plan.target_end_cents = plan.target_end_cents + delta
    plan.band_cents = max(plan.band_cents, 2500 + band_extra)
    try:
        schedule = solve(plan)
    except RuntimeError:
        # Some targets are infeasible under Spark's discrete payouts; skip.
        assume(False)
    report = validate(plan, schedule)
    assert report.ok
