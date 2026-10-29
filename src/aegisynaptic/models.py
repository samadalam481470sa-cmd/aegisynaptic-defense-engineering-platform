"""Physics-informed simulation and reproducible synthetic asset inventory."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import exp
from random import Random

@dataclass(frozen=True)
class Asset:
    id: str
    name: str
    kind: str
    temperature_c: float
    vibration_mm_s: float
    degradation: float
    load: float
    cooling: float
    capacity_kw: float

ASSETS = [
    Asset("GEN-101", "North Grid Generator", "generator", 72, 5.3, .36, .78, .87, 280),
    Asset("GEN-102", "South Grid Generator", "generator", 61, 3.7, .21, .64, .94, 320),
    Asset("HVAC-201", "Primary Cooling Array", "cooling", 80, 6.8, .57, .92, .66, 170),
    Asset("HVAC-202", "Secondary Cooling Array", "cooling", 57, 2.8, .16, .51, .96, 190),
    Asset("UPS-301", "Energy Storage Controller", "electrical", 66, 4.1, .29, .69, .93, 130),
    Asset("NET-401", "Communications Rack Cooling", "cooling", 84, 6.3, .66, .86, .60, 45),
    Asset("PUMP-501", "Circulation Pump Alpha", "mechanical", 69, 5.0, .42, .80, .84, 65),
    Asset("PUMP-502", "Circulation Pump Beta", "mechanical", 55, 2.5, .13, .49, .96, 65),
]
BY_ID = {a.id: a for a in ASSETS}

@dataclass
class State:
    temperature_c: float
    vibration_mm_s: float
    degradation: float

def step(asset: Asset, state: State, rng: Random, dt_hours: float = 1.0,
         ambient_c: float = 26.0, load: float | None = None) -> State:
    """Euler discretization of a deliberately simplified coupled thermo-mechanical system."""
    if not 0 < dt_hours <= 24:
        raise ValueError("dt_hours must be in (0,24]")
    duty = asset.load if load is None else max(0., min(1.5, load))
    thermal_drift = (.055 * (ambient_c - state.temperature_c)
                     + 3.4 * duty - 1.5 * asset.cooling)
    temp = max(-20., min(160., state.temperature_c + dt_hours * thermal_drift
                               + rng.gauss(0, .19) * dt_hours**.5))
    wear_increment = dt_hours * .00016 * (max(.01, duty) ** 1.8) * exp(
        max(-4., min(4., (temp - 65.) / 38.)))
    shock = rng.expovariate(1/.002) if rng.random() < .002 * dt_hours else 0.
    wear = max(0., min(1.5, state.degradation + wear_increment + shock))
    vibration = max(.05, .64 * state.vibration_mm_s
                    + .36 * (1.0 + 7 * wear + 1.3 * duty)
                    + rng.gauss(0, .12))
    return State(round(temp, 4), round(vibration, 4), round(wear, 6))

def initial_state(asset: Asset) -> State:
    return State(asset.temperature_c, asset.vibration_mm_s, asset.degradation)

def telemetry(asset: Asset, steps: int = 96, seed: int = 11) -> list[dict]:
    """A stable stream, useful for demos; never represents real equipment readings."""
    if not 1 <= steps <= 2000:
        raise ValueError("steps must be between 1 and 2000")
    rng = Random(seed + sum(map(ord, asset.id)))
    state = initial_state(asset)
    samples = []
    for hour in range(steps):
        cycle_load = max(.15, min(1.0, asset.load + .16 * __import__('math').sin(hour / 8)))
        state = step(asset, state, rng, dt_hours=.25, load=cycle_load)
        samples.append({"sample": hour, "hours": round(hour * .25, 2),
                        **asdict(state), "load": round(cycle_load, 3)})
    return samples
