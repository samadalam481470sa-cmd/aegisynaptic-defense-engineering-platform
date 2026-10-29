"""Resource-constrained advisory maintenance optimizer (0/1 dynamic program)."""
from __future__ import annotations
from dataclasses import dataclass
from .analytics import fleet_analysis
from .models import BY_ID

@dataclass(frozen=True)
class Job:
    asset_id: str
    cost_units: int
    duration_hours: int
    benefit: int

def candidate_jobs() -> list[Job]:
    scores = {a["id"]: a for a in fleet_analysis()["assets"]}
    jobs = []
    for key, a in BY_ID.items():
        x = scores[key]
        cost = max(1, round(2 + a.capacity_kw / 100))
        duration = max(1, round(1 + a.degradation * 7))
        benefit = max(1, round(100 * x["propagated_risk"] + 30 * x["anomaly_score"]))
        jobs.append(Job(key, cost, duration, benefit))
    return jobs

def optimize(budget: int = 12, labor_hours: int = 20) -> dict:
    if not 0 <= budget <= 500 or not 0 <= labor_hours <= 500:
        raise ValueError("budget and labor_hours must be in 0..500")
    jobs = candidate_jobs()
    # Pareto frontier over two capacities; each job is processed once.
    states: dict[tuple[int,int], tuple[int, tuple[str,...]]] = {(0,0): (0, ())}
    for job in jobs:
        next_states = dict(states)
        for (cost, hours), (benefit, selected) in states.items():
            new_cost, new_hours = cost + job.cost_units, hours + job.duration_hours
            if new_cost > budget or new_hours > labor_hours:
                continue
            key = (new_cost, new_hours)
            proposal = (benefit + job.benefit, selected + (job.asset_id,))
            if key not in next_states or proposal[0] > next_states[key][0]:
                next_states[key] = proposal
        states = next_states
    (used_cost, used_hours), (benefit, selected) = max(
        states.items(), key=lambda row: (row[1][0], -row[0][0], -row[0][1]))
    return {"budget": budget, "labor_hours": labor_hours, "used_budget": used_cost,
            "used_labor_hours": used_hours, "score_improvement": benefit,
            "selected_asset_ids": selected,
            "candidates": [vars(j) for j in jobs],
            "advisory_only": True}
