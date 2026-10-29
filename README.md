# AEGISYNAPTIC
**Autonomous Engineering Grid for Intelligent Systems, Yield Analysis, Network Assurance, Predictive Technology & Infrastructure Coordination**

An unclassified **defense-infrastructure reliability engineering demonstrator** for predictive maintenance, stochastic simulation, dependency risk, and optimization. Uses *synthetic equipment and sensor data only*. It does not control weapons, target people, or connect to operational military systems.

## Capabilities
- Coupled thermal, vibration, and degradation digital twin with stochastic telemetry
- Remaining-useful-life Monte Carlo estimation and survival quantiles
- Robust streaming anomaly scoring using median absolute deviation and EWMA
- Directed dependency graph and criticality propagation
- Resource-constrained maintenance optimization using dynamic programming
- FastAPI services for fleet summary, telemetry, simulation, and recommendations
- Accessible browser dashboard with native canvas charts
- Reproducible tests and Docker / GitHub Actions

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn aegisynaptic.api:app --reload
```
Open http://localhost:8000/ for the dashboard, and http://localhost:8000/docs for the interactive API.

```bash
pytest -q
docker compose up --build
```

## API
| Route | Purpose |
|---|---|
| `GET /api/health` | Service health |
| `GET /api/assets` | Synthetic assets and current readings |
| `GET /api/fleet/analysis` | Health, anomaly, risk, dependencies |
| `GET /api/assets/{id}/telemetry` | Synthetic telemetry history |
| `POST /api/assets/{id}/simulate` | Monte Carlo RUL and confidence intervals |
| `POST /api/maintenance/optimize` | Risk-weighted maintenance resource allocation |
| `GET /api/architecture` | Model and limitations |

## Engineering model
Discrete thermal dynamics: `T(t+dt)=T+dt*(ambient_gain*(Ta-T)+load_gain*L-cooling_gain*C)+noise`.
Cumulative mechanical degradation: `D(t+dt)=clip(D+dt*k*L^p*exp((T-Tref)/Tscale)+shock,0,1.5)`.
Risk is a transparent non-calibrated heuristic derived from degradation, temperature, vibration, and propagated dependency exposure; it is **not a certified failure probability**.
Monte Carlo forecasts sample varying duty cycles, ambient conditions, and process noise; percentile ranges express simulated model variation rather than validated field reliability.

## Safety and production limitations
This prototype has no external integrations, no real asset telemetry, no authentication or persistent database; it must not be deployed to an exposed network. The optimization is advisory only. Engineering and cybersecurity validation, calibration to authorized field data, authentication, audit records, durable storage, and independent safety review are required before any actual use. It is not approved for safety-critical decision-making.

## Roadmap
1. Calibrated prognostic models and offline evaluation datasets.
2. PostgreSQL/TimescaleDB ingestion with signed device identity.
3. OIDC, organization-level RBAC, audit logging, and rate limiting.
4. Distributed simulation workers and Kubernetes deployment.
5. Explainability and measured accuracy dashboards.
