# Self-Adaptive-Observability-Platform-
Real-time anomaly-triggered telemetry control for cost optimization and debugging efficiency.

# Architecture 

                              +------------------+
                              |     GRAFANA      |
                              |   (Dashboards)   |
                              +---------^--------+
                                        |
                                        | reads
                             +----------+----------+
                             |      PROMETHEUS     |
                             |   (time-series DB)  |
                             +----------^----------+
                                        | scrape /metrics
               +------------------------+------------------------+
               |                                                 |
               |                                                 |
        +------+-------+                                 +------+-------+
        |    VECTOR    |                                 |  CONTROLLER  |
        |  (Pipeline)  |                                 | (FastAPI/Go) |
        | ingest->enrich->redact->sample->route          +------+-------+
        +--^-------^---+                                        |
           |       |                                            | writes config
           |       |                                            v
           |       +------------------> logs/traces files   [vector.generated.toml]
           |
           | DogStatsD / OTLP / TCP
   +-------+------+                          +-----------------+
   |   GO API     |                          |  PYTHON WORKER  |
   | (OTel+StatsD)|                          | (OTel+StatsD)   |
   +--------------+                          +-----------------+
           ^
           |
      LOAD GENERATOR (k6 / wrk)
