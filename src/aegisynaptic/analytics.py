"""Explainable anomaly detection, dependency analysis, survival simulation."""
from __future__ import annotations
from math import exp
from random import Random
from statistics import median
from .models import ASSETS, BY_ID, Asset, initial_state, step, telemetry

DEPENDENCIES = {
    "GEN-101": ["UPS-301"], "GEN-102": ["UPS-301"],
    "HVAC-201": ["NET-401", "PUMP-501"],
    "HVAC-202": ["NET-401"],
    "UPS-301": ["NET-401"],
    "PUMP-501": ["HVAC-201"],
    "PUMP-502": ["HVAC-202"],
    "NET-401": [],
}
# The diagram can contain cycles; iterative decay keeps dependency influence bounded.
def anomaly_score(values: list[float]) -> float:
    if len(values) < 5:
        return 0.
    reference = values[:-1]
    center = median(reference)
    mad = median([abs(v - center) for v in reference])
    robust_z = abs(values[-1] - center) / max(.08, 1.4826 * mad)
    return round(min(1., robust_z / 6.), 4)

def intrinsic_risk(a: Asset) -> float:
    """Heuristic score, NOT a calibrated probability of failure."""
    z = (3.4 * a.degradation + .028 * max(0, a.temperature_c - 60)
         + .16 * max(0, a.vibration_mm_s - 3) - 2.0)
    return round(1 / (1 + exp(-z)), 5)

def propagation(risks: dict[str, float], iterations: int = 7) -> dict[str, float]:
    """Bounded risk spreading through impacted dependency nodes."""
    result = dict(risks)
    for _ in range(iterations):
        nxt = dict(risks)
        for source, targets in DEPENDENCIES.items():
            for target in targets:
                nxt[target] = max(nxt[target], min(.99, risks[target]
                                  + .18 * result[source] * (1 - risks[target])))
        result = nxt
    return {k: round(v, 5) for k, v in result.items()}

def fleet_analysis() -> dict:
    raw = {a.id: intrinsic_risk(a) for a in ASSETS}
    network = propagation(raw)
    assets = []
    for a in ASSETS:
        history = telemetry(a, steps=72)
        anomaly = anomaly_score([x["vibration_mm_s"] for x in history])
        health = max(0, round(100 * (1 - .78 * network[a.id] - .22 * anomaly), 1))
        assets.append({"id": a.id, "name": a.name, "kind": a.kind,
                       "health": health, "risk_score": raw[a.id],
                       "propagated_risk": network[a.id],
                       "anomaly_score": anomaly, "temperature_c": a.temperature_c,
                       "vibration_mm_s": a.vibration_mm_s,
                       "dependencies": DEPENDENCIES[a.id],
                       "status": "critical" if health < 45 else "watch" if health < 70 else "healthy"})
    assets.sort(key=lambda a: a["health"])
    return {"synthetic": True, "assets": assets,
            "fleet_health": round(sum(a["health"] for a in assets) / len(assets), 1),
            "watch_count": sum(a["status"] != "healthy" for a in assets),
            "dependencies": [{"from": src, "to": target}
                             for src, targets in DEPENDENCIES.items() for target in targets]}

def remaining_useful_life(asset: Asset, trials: int = 160, horizon_hours: int = 1500,
                          seed: int = 73) -> dict:
    """Independent stochastic digital-twin trajectories and empirical RUL quantiles."""
    if not 20 <= trials <= 1000 or not 1 <= horizon_hours <= 10000:
        raise ValueError("trials must be 20..1000 and horizon_hours 1..10000")
    rng = Random(seed)
    failures = []
    censored = 0
    for _ in range(trials):
        state = initial_state(asset)
        ambient = rng.uniform(19, 37)
        duty = max(.15, min(1.2, rng.gauss(asset.load, .13)))
        elapsed = 0
        while elapsed < horizon_hours and state.degradation < 1.0:
            dt = min(8, horizon_hours - elapsed)
            state = step(asset, state, rng, dt_hours=dt, ambient_c=ambient, load=duty)
            elapsed += dt
        failures.append(elapsed)
        censored += int(state.degradation < 1.0)
    failures.sort()
    def q(p: float) -> int:
        return failures[min(trials - 1, round((trials - 1) * p))]
    return {"asset_id": asset.id, "trials": trials, "horizon_hours": horizon_hours,
            "p10_hours": q(.1), "median_hours": q(.5), "p90_hours": q(.9),
            "censored_trials": censored, "threshold": 1.0, "synthetic": True,
            "note": "Horizon-censored simulation, not validated field reliability."}
