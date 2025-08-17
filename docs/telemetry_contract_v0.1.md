# Telemetry Contract v0.1

## 0) Portée & Objectifs
- **Portée** : 
  - Métriques **DogStatsD → Vector → Prometheus**
  - Logs **JSON TCP → Vector → NDJSON**
- **Objectifs** : 
  - Avoir des noms et formats **stables**
  - Faciliter la création de dashboards et d’alertes
  - Éviter la dérive (labels uniques, renommages sauvages)

---

## 1) Conventions
- Les **counters** finissent par `*_total`.
- Les **unités** suivent les conventions Prometheus :  
  - `*_seconds` pour des durées  
  - `*_bytes` pour des tailles  
- **Labels autorisés (v0.1)** : `service`, `env`  
- **Interdit en labels** : IDs uniques (`trace_id`, `user_id`, etc.) → risque de cardinalité élevée.

---

## 2) Métriques (v0.1)

| Nom Prometheus                 | Type    | Source StatsD           | Labels            | Signification                                    |
|--------------------------------|---------|-------------------------|-------------------|--------------------------------------------------|
| `api_requests_total`           | Counter | `api.requests`          | `service`, `env`  | Nombre total de requêtes traitées                |
| `api_errors_total`             | Counter | (à ajouter côté Go API) | `service`, `env`  | Nombre total de requêtes échouées (status ≥ 500) |
| `api_request_duration_ms_sum`  | Counter | `api.request_duration_ms` | `service`, `env` | Somme des durées (ms) de traitement des requêtes |
| `api_request_duration_ms_count`| Counter | `api.request_duration_ms` | `service`, `env` | Nombre de mesures de latence collectées          |

> ℹ️ La latence est en millisecondes (StatsD timer).  
> En v0.2, elle pourra migrer vers un **histogramme en secondes** pour calculer p95/p99 proprement.

---

## 3) Schéma des logs (NDJSON)

- **Format** : une ligne = un objet JSON complet.  
- **Champs obligatoires (v0.1)** :
  - `time` (RFC3339)
  - `level` (`debug|info|warn|error`)
  - `msg` (texte court)
  - `service` (ex. `"api"`)
  - `env` (ex. `"dev"`)
  - `path` (ex. `"/hello"`)
  - `status` (code HTTP)
  - `latency_ms` (float)

- **Champs futurs (v0.2)** :
  - `version`
  - `trace_id` (corrélation, jamais en label Prometheus)

**Exemple :**
```json
{"time":"2025-08-17T18:02:03Z","level":"info","msg":"handled request","service":"api","env":"dev","path":"/","status":200,"latency_ms":12.0}

## 4) Pipeline attendu

- **Vector Sources** :
  - `statsd_metrics` (UDP 8125, `use_tags: true`) → métriques DogStatsD
  - `app_logs` (TCP 9000, `codec: json`) → logs JSON

- **Vector Sinks** :
  - `prometheus_exporter` (HTTP 9090) → exposition des métriques pour Prometheus
  - `file` → `/var/log/app-logs.ndjson` (stockage local des logs NDJSON)

- **Prometheus** :
  - Scrape de `vector:9090` toutes les **2s**

---

## 5) Requêtes PromQL de validation

1. **Requests/s par service**
```promql
sum(rate(api_requests_total[5m])) by (service)



