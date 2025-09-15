from hypothesis import given, settings, strategies as st

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.validate import validate


@settings(max_examples=10, deadline=None)
@given(
    delta=st.integers(min_value=-10, max_value=10).map(lambda k: k * 100),  # multiples of $100
    band_extra=st.integers(min_value=0, max_value=2000),  # widen band modestly
)
def test_randomized_target_and_band_keeps_validity(delta, band_extra):
    plan = load_plan("plan.json")
    # Adjust target modestly and keep band at least canonical + extra
    plan.target_end_cents = plan.target_end_cents + delta
    plan.band_cents = max(plan.band_cents, 10000 + band_extra)
    schedule = solve(plan)
    report = validate(plan, schedule)
    assert report.ok
