"""HTTP interface: synthetic data only; bind to loopback for local development."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .models import ASSETS, BY_ID, telemetry
from .analytics import fleet_analysis, remaining_useful_life
from .optimization import optimize

app = FastAPI(title="AEGISYNAPTIC", version="0.1.0",
              description="Unclassified synthetic infrastructure reliability engineering demonstrator")

class SimulationRequest(BaseModel):
    trials: int = Field(default=160, ge=20, le=1000)
    horizon_hours: int = Field(default=1500, ge=1, le=10000)
    seed: int = 73

class OptimizationRequest(BaseModel):
    budget: int = Field(default=12, ge=0, le=500)
    labor_hours: int = Field(default=20, ge=0, le=500)

def find_asset(asset_id: str):
    asset = BY_ID.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Unknown synthetic asset")
    return asset

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "synthetic", "version": "0.1.0"}

@app.get("/api/assets")
def assets():
    return {"synthetic": True, "assets": [vars(a) for a in ASSETS]}

@app.get("/api/fleet/analysis")
def analysis():
    return fleet_analysis()

@app.get("/api/assets/{asset_id}/telemetry")
def history(asset_id: str, samples: int = Query(default=96, ge=1, le=2000)):
    a = find_asset(asset_id)
    return {"asset_id": asset_id, "synthetic": True, "samples": telemetry(a, steps=samples)}

@app.post("/api/assets/{asset_id}/simulate")
def simulate(asset_id: str, request: SimulationRequest):
    return remaining_useful_life(find_asset(asset_id), **request.model_dump())

@app.post("/api/maintenance/optimize")
def maintenance(request: OptimizationRequest):
    return optimize(**request.model_dump())

@app.get("/api/architecture")
def architecture():
    return {"models": ["thermo-mechanical Euler digital twin", "robust MAD anomaly scoring",
                       "iterative dependency-risk spreading", "Monte Carlo RUL",
                       "two-resource 0/1 dynamic programming"],
            "limitations": ["synthetic data", "uncalibrated risk", "no authentication",
                            "no production deployment", "advisory only"]}
