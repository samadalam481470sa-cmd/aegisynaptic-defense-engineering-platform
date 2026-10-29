from random import Random
import pytest
from aegisynaptic.models import ASSETS, initial_state, step, telemetry
from aegisynaptic.analytics import (anomaly_score, fleet_analysis,
                                      remaining_useful_life, propagation)
from aegisynaptic.optimization import optimize

def test_telemetry_is_reproducible():
    assert telemetry(ASSETS[0], 15) == telemetry(ASSETS[0], 15)

def test_invalid_step_rejected():
    with pytest.raises(ValueError):
        step(ASSETS[0], initial_state(ASSETS[0]), Random(1), dt_hours=-1)

def test_risk_is_bounded():
    fleet = fleet_analysis()
    assert len(fleet["assets"]) == len(ASSETS)
    assert all(0 <= a["propagated_risk"] <= 1 for a in fleet["assets"])

def test_propagation_non_decreasing():
    initial = {a.id: .1 for a in ASSETS}
    result = propagation(initial)
    assert all(result[key] >= initial[key] for key in initial)

def test_robust_anomaly():
    assert anomaly_score([1, 1, 1, 1, 1, 10]) > .9

def test_monte_carlo_repeatable():
    a = ASSETS[0]
    p = remaining_useful_life(a, 20, 120, 5)
    assert p == remaining_useful_life(a, 20, 120, 5)
    assert p["p10_hours"] <= p["median_hours"] <= p["p90_hours"]

def test_zero_budget():
    x = optimize(0, 0)
    assert x["selected_asset_ids"] == ()
    assert x["score_improvement"] == 0

def test_optimizer_honors_capacity():
    x = optimize(9, 10)
    assert x["used_budget"] <= 9
    assert x["used_labor_hours"] <= 10

def test_invalid_optimizer_rejected():
    with pytest.raises(ValueError):
        optimize(-1, 4)
