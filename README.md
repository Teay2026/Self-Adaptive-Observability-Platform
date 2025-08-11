# Self-Adaptive-Observability-Platform-
Real-time anomaly-triggered telemetry control for cost optimization and debugging efficiency.

# Architecture 

## Architecture Diagram

```mermaid
flowchart LR
  subgraph Apps
    API[Go API\nOTel + DogStatsD]
    Worker[Python Worker\nOTel + DogStatsD]
  end

  LoadGen[Load Generator\n(k6/wrk)] --> API

  API -->|metrics/logs/traces| Vector
  Worker -->|metrics/logs/traces| Vector

  Vector[[Vector Pipeline\ningest → enrich → redact → sample → route]]
  Vector -->|/metrics| Prometheus[(Prometheus TSDB)]
  Prometheus -->|reads| Grafana[Grafana Dashboards]

  Controller[Controller\n(FastAPI/Go)]
  Controller -- PromQL polls --> Prometheus
  Controller -- write config + reload --> Vector

  Vector -->|logs/traces| Files[(File sinks)]
```

