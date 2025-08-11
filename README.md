# Self-Adaptive-Observability-Platform-
Real-time anomaly-triggered telemetry control for cost optimization and debugging efficiency.

# Architecture 

                           ┌──────────────────────────────────────────────────┐
                           │                GRAFANA (Dashboards)              │
                           │  - Service Health (RED)                          │
                           │  - Pipeline KPIs + Mode Annotations              │
                           └───────────────▲──────────────────────────────────┘
                                           │  (reads)
                                           │
                                   ┌───────┴────────┐
                                   │  PROMETHEUS    │
                                   │  (Time-series) │
                                   │  - Scrapes Vector / App metrics
                                   └───────▲────────┘
                                           │  (scrape /metrics)
                  ┌────────────────────────┼────────────────────────┐
                  │                        │                        │
                  │                        │                        │
        ┌─────────┴─────────┐      ┌───────┴────────┐      ┌───────┴────────┐
        │   VECTOR (Pipeline)│      │  CONTROLLER    │      │  LOAD GENERATOR│
        │  Ingest→Transform  │      │  (FastAPI/Go)  │      │   (wrk/k6)     │
        │  →Redact→Sample→   │      │ - Poll PromQL  │      └────────────────┘
        │  Route             │      │ - Decide policy (LOW/HIGH)      
        │ Sources:           │      │ - Rewrite vector config + reload
        │  - DogStatsD :8125 │      │ - Emit decision events
        │  - OTLP HTTP :4318 │      └───────────┬────────────────────────────┐
        │  - TCP logs :9000  │                  │ (hot reload / file swap)    │
        │ Sinks:             │                  │                             │
        │  - Prom exporter   │  writes          │                             │
        │  - File (logs)     │  vector.generated.toml                          │
        │  - File (traces)   │                                                │
        └─────────▲──────────┘                                                │
                  │ (DogStatsD / OTLP / TCP)                                   │
     ┌────────────┼───────────────────────────────────────────────────────────┐│
     │            │                                                           ││
┌────┴─────┐  ┌───┴─────┐                                                     ││
│  GO API  │  │ PY WORK │   (Structured JSON logs, metrics, traces)           ││
│  /ok     │  │ jobs    │─────────────────────────────────────────────────────┘│
│  /slow   │  │ +fail   │
│  /error  │  │         │
│  OTel +  │  │ OTel +  │
│  DogStats│  │ DogStats│
└──────────┘  └─────────┘
