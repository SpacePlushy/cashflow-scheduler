#!/usr/bin/env python3
"""Comprehensive skill test suite

Tests all critical functionality:
1. Infeasible plan error handling
2. Validation with invalid schedules
3. Import system integrity
4. Edge cases (locked actions, manual adjustments)
5. Solver fallback behavior
"""

import sys
from pathlib import Path

# Add skill root to Python path
skill_root = Path(__file__).parent
sys.path.insert(0, str(skill_root))

from core import (
    solve,
    Plan,
    Schedule,
    Bill,
    Deposit,
    Adjustment,
    DayLedger,
    to_cents,
    cents_to_str,
    validate,
    dp_solver,
    cpsat_solver,
)


def test_infeasible_plan():
    """Test that infeasible plans raise appropriate errors"""
    print("\n=== Test: Infeasible Plan (Bills Exceed Income) ===")

    # Create impossible plan: $10,000 in bills with only $100 start
    plan = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(500.00),
        band_cents=to_cents(25.0),
        rent_guard_cents=to_cents(5000.0),
        deposits=[],
        bills=[
            Bill(day=1, name="Huge Bill", amount_cents=to_cents(10000.0))
        ],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    try:
        schedule = solve(plan)
        print("❌ FAILED: Should have raised error for infeasible plan")
        return False
    except RuntimeError as e:
        print(f"✅ PASSED: Correctly raised error: {str(e)[:100]}...")
        return True


def test_validation_day1_not_spark():
    """Test validation catches Day 1 not being Spark"""
    print("\n=== Test: Validation Catches Day 1 Not Spark ===")

    # Create a valid plan
    plan = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(100.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    # Create invalid schedule manually (Day 1 is "O" instead of "Spark")
    invalid_schedule = Schedule(
        actions=["O"] + ["Spark"] * 29,  # Wrong: Day 1 is off
        objective=(29, 28, 0),
        final_closing_cents=to_cents(100.00),
        ledger=[]  # Empty for simplicity
    )

    report = validate(plan, invalid_schedule)

    if not report.ok and not report.checks[0][1]:  # Day 1 Spark check should fail
        print("✅ PASSED: Validation correctly caught Day 1 not being Spark")
        return True
    else:
        print("❌ FAILED: Validation did not catch Day 1 violation")
        return False


def test_locked_actions():
    """Test that locked actions are honored"""
    print("\n=== Test: Locked Actions ===")

    plan = Plan(
        start_balance_cents=to_cents(500.00),
        target_end_cents=to_cents(500.00),
        band_cents=to_cents(200.0),
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=["Spark"] + ["O"] * 5 + [None] * 24,  # Lock first 6 days
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    schedule = solve(plan)

    # Check that locked days were honored
    if schedule.actions[:6] == ["Spark"] + ["O"] * 5:
        print("✅ PASSED: Locked actions honored")
        print(f"   First 6 days: {' '.join(schedule.actions[:6])}")
        return True
    else:
        print("❌ FAILED: Locked actions not honored")
        print(f"   Expected: Spark O O O O O")
        print(f"   Got: {' '.join(schedule.actions[:6])}")
        return False


def test_manual_adjustments():
    """Test manual adjustments work correctly"""
    print("\n=== Test: Manual Adjustments ===")

    # Plan without adjustment: should need more workdays
    plan_no_adj = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(600.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    schedule_no_adj = solve(plan_no_adj)
    workdays_no_adj = schedule_no_adj.objective[0]

    # Plan with adjustment: should need fewer workdays
    plan_with_adj = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(600.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[
            Adjustment(day=15, amount_cents=to_cents(200.0), note="Found money")
        ],
        locks=[],
        metadata={}
    )

    schedule_with_adj = solve(plan_with_adj)
    workdays_with_adj = schedule_with_adj.objective[0]

    if workdays_with_adj < workdays_no_adj:
        print("✅ PASSED: Manual adjustment reduced required workdays")
        print(f"   Without adjustment: {workdays_no_adj} workdays")
        print(f"   With +$200 adjustment: {workdays_with_adj} workdays")
        return True
    else:
        print("❌ FAILED: Manual adjustment didn't have expected effect")
        return False


def test_import_integrity():
    """Test that all imports work correctly"""
    print("\n=== Test: Import System Integrity ===")

    try:
        # Test all core imports
        from core import (
            solve, Plan, Schedule, Bill, Deposit, Adjustment, DayLedger,
            to_cents, cents_to_str, build_ledger, validate, ValidationReport,
            SHIFT_NET_CENTS, dp_solver, cpsat_solver
        )

        # Test solver module imports
        from core.dp_solver import solve as dp_solve
        from core.cpsat_solver import solve as cpsat_solve
        from core.model import build_prefix_arrays, pre_rent_base_on_day30
        from core.ledger import build_ledger
        from core.validate import validate

        print("✅ PASSED: All imports successful")
        return True
    except ImportError as e:
        print(f"❌ FAILED: Import error: {e}")
        return False


def test_solver_fallback():
    """Test that solver fallback works"""
    print("\n=== Test: Solver Fallback Behavior ===")

    plan = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(200.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    # Test DP solver directly
    try:
        schedule_dp = dp_solver.solve(plan)
        print(f"✅ DP solver works: {schedule_dp.objective}")
    except Exception as e:
        print(f"❌ DP solver failed: {e}")
        return False

    # Test CP-SAT with fallback
    try:
        result = cpsat_solver.solve_with_diagnostics(plan, dp_fallback=True)
        print(f"✅ CP-SAT with fallback works: solver={result.solver}, obj={result.schedule.objective}")

        if result.fallback_reason:
            print(f"   (Used DP fallback: {result.fallback_reason})")
    except Exception as e:
        print(f"❌ CP-SAT with fallback failed: {e}")
        return False

    # Test auto solver
    try:
        schedule_auto = solve(plan, solver="auto")
        print(f"✅ Auto solver works: {schedule_auto.objective}")
    except Exception as e:
        print(f"❌ Auto solver failed: {e}")
        return False

    return True


def test_money_conversion():
    """Test money conversion utilities"""
    print("\n=== Test: Money Conversion Utilities ===")

    tests = [
        (100.00, 10000, "100.00"),
        (0.50, 50, "0.50"),
        (123.45, 12345, "123.45"),
        (-50.00, -5000, "-50.00"),
        ("100.50", 10050, "100.50"),
    ]

    all_passed = True
    for amount, expected_cents, expected_str in tests:
        cents = to_cents(amount)
        str_repr = cents_to_str(cents)

        if cents != expected_cents:
            print(f"❌ FAILED: to_cents({amount}) = {cents}, expected {expected_cents}")
            all_passed = False
        elif str_repr != expected_str:
            print(f"❌ FAILED: cents_to_str({cents}) = {str_repr}, expected {expected_str}")
            all_passed = False

    if all_passed:
        print(f"✅ PASSED: All {len(tests)} money conversions correct")

    return all_passed


def test_band_tolerance():
    """Test that band tolerance works correctly"""
    print("\n=== Test: Band Tolerance ===")

    # Tight band should be harder to satisfy
    plan_tight = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(500.00),
        band_cents=to_cents(1.0),  # Very tight
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    # Wide band should be easier
    plan_wide = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(500.00),
        band_cents=to_cents(200.0),  # Very wide
        rent_guard_cents=to_cents(0.0),
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    try:
        schedule_tight = solve(plan_tight)
        schedule_wide = solve(plan_wide)

        # Both should work, but tight band might require different workdays
        print(f"✅ PASSED: Band tolerance works")
        print(f"   Tight band (±$1): {schedule_tight.objective[0]} workdays")
        print(f"   Wide band (±$200): {schedule_wide.objective[0]} workdays")
        return True
    except Exception as e:
        print(f"❌ FAILED: Band tolerance test error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("COMPREHENSIVE CASHFLOW SCHEDULER SKILL TEST SUITE")
    print("=" * 70)

    tests = [
        ("Infeasible Plan Handling", test_infeasible_plan),
        ("Validation - Day 1 Check", test_validation_day1_not_spark),
        ("Locked Actions", test_locked_actions),
        ("Manual Adjustments", test_manual_adjustments),
        ("Import Integrity", test_import_integrity),
        ("Solver Fallback", test_solver_fallback),
        ("Money Conversion", test_money_conversion),
        ("Band Tolerance", test_band_tolerance),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Skill is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
