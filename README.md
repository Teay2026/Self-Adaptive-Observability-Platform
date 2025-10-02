
# 🚀 Self-Adaptive Observability Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Compatible-orange.svg)](https://prometheus.io/)
[![Go](https://img.shields.io/badge/Go-1.22+-00ADD8.svg)](https://golang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org/)

> **Intelligent observability platform that automatically adjusts data collection rates based on real-time system conditions, reducing costs by 60-90% while maintaining incident detection capability.**

## 🎯 **Problem Statement**

Traditional observability systems face a critical dilemma:
- **Static sampling**: Wastes money collecting unused data during normal operations
- **High sampling**: Expensive but ensures incident visibility
- **Low sampling**: Cost-effective but risks missing critical events
- **Manual tuning**: Time-intensive and reactive, not predictive

**Result**: Organizations spend millions on observability data they never use, while missing the 20% that matters during incidents.

## 💡 **The Solution**

The **Self-Adaptive Observability Platform** implements a **closed-loop control system** that automatically adjusts data sampling rates based on real-time system health metrics.

### **Core Innovation: Control Theory Applied to Observability**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   SENSOR    │───▶│ CONTROLLER   │───▶│   ACTUATOR      │
│(Prometheus) │    │(Python App)  │    │(Sampling Rate)  │
└─────────────┘    └──────────────┘    └─────────────────┘
       ▲                                        │
       │            ┌──────────────┐           │
       └────────────│    PLANT     │◀──────────┘
                    │  (Go API)    │
                    └──────────────┘
```

**Adaptive Logic:**
- 🔴 **High errors OR high latency** → Increase sampling (more visibility)
- 🟢 **Low errors AND low latency** → Decrease sampling (cost optimization)
- ⏱️ **Real-time response** → 3-second polling + instant webhook reactions
- 🛡️ **Stability controls** → Cooldown periods prevent oscillation

## 🏗️ **Architecture Overview**

### **System Components**

| Service | Technology | Purpose | Port | Key Features |
|---------|------------|---------|------|--------------|
| **Controller** | Python/Flask | Decision engine with control algorithms | 9095 | Real-time metrics analysis, adaptive control logic |
| **Go API** | Go/HTTP | Target application with adaptive sampling | 8080 | StatsD/TCP logging, sampling rate control |
| **Vector** | Rust | High-performance data pipeline | 9090 | Log aggregation, metrics forwarding |
| **Prometheus** | Go | Time-series database and query engine | 9091 | Metrics storage, PromQL queries |
| **AlertManager** | Go | Alert routing and webhook delivery | 9093 | Critical event notifications |
| **Grafana** | TypeScript | Visualization and dashboards | 3000 | Real-time monitoring, custom dashboards |
| **Demo UI** | Python/Flask | Real-time monitoring interface | 8081 | System status, manual controls |
| **Webhook** | Python/Flask | AlertManager webhook receiver | 9094 | Alert processing and logging |

### **Detailed Architecture Schema**

```mermaid
graph TB
    subgraph "External Access"
        USER[👤 User]
        BROWSER[🌐 Browser]
    end
    
    subgraph "Presentation Layer"
        GRAFANA[📊 Grafana<br/>Port 3000<br/>Dashboards & Viz]
        DEMO[🖥️ Demo UI<br/>Port 8081<br/>Control Interface]
    end
    
    subgraph "Control Loop (Core Innovation)"
        CONTROLLER[🧠 Controller<br/>Port 9095<br/>Python Flask<br/>- Adaptive Algorithm<br/>- Real-time Analysis<br/>- Control Decisions]
    end
    
    subgraph "Monitoring & Alerting"
        PROMETHEUS[📈 Prometheus<br/>Port 9091<br/>- Metrics Storage<br/>- PromQL Queries<br/>- Scraping]
        ALERTMGR[🚨 AlertManager<br/>Port 9093<br/>- Alert Routing<br/>- Webhooks]
        WEBHOOK[📞 Webhook Service<br/>Port 9094<br/>- Alert Processing]
    end
    
    subgraph "Data Pipeline"
        VECTOR[⚡ Vector<br/>Port 9090<br/>- Log Aggregation<br/>- Metrics Pipeline<br/>- Data Transformation]
    end
    
    subgraph "Target Application"
        GOAPI[🎯 Go API<br/>Port 8080<br/>- HTTP Server<br/>- Adaptive Sampling<br/>- Metrics Generation]
    end
    
    subgraph "Data Storage"
        LOGS[(📝 Log Files)]
        METRICS[(📊 Time Series DB)]
    end
    
    %% User Interactions
    USER -.-> BROWSER
    BROWSER --> GRAFANA
    BROWSER --> DEMO
    
    %% Control Flow (Primary)
    PROMETHEUS -->|PromQL Queries<br/>Error Rate & Latency| CONTROLLER
    CONTROLLER -->|HTTP API<br/>Sampling Rate| GOAPI
    
    %% Alert Flow (Secondary)
    PROMETHEUS -->|Alert Rules| ALERTMGR
    ALERTMGR -->|Webhook| WEBHOOK
    ALERTMGR -->|Fast Response| CONTROLLER
    
    %% Data Flow
    GOAPI -->|HTTP Metrics<br/>Scrape Target| PROMETHEUS
    GOAPI -->|StatsD/UDP<br/>TCP Logs| VECTOR
    VECTOR -->|Metrics Export| PROMETHEUS
    VECTOR -->|File Output| LOGS
    PROMETHEUS --> METRICS
    
    %% Monitoring Flow
    CONTROLLER -->|Self Metrics| PROMETHEUS
    DEMO -->|Status API| CONTROLLER
    GRAFANA -->|PromQL| PROMETHEUS
    
    %% Styling
    classDef controller fill:#ff9999,stroke:#ff0000,stroke-width:3px
    classDef monitoring fill:#99ccff,stroke:#0066cc,stroke-width:2px
    classDef application fill:#99ff99,stroke:#00cc00,stroke-width:2px
    classDef presentation fill:#ffcc99,stroke:#ff9900,stroke-width:2px
    classDef storage fill:#cc99ff,stroke:#9900cc,stroke-width:2px
    
    class CONTROLLER controller
    class PROMETHEUS,ALERTMGR,WEBHOOK monitoring
    class GOAPI,VECTOR application
    class GRAFANA,DEMO presentation
    class LOGS,METRICS storage
```

### **Control System Flow**

```
┌─────────────────┐    Sensor     ┌─────────────────┐
│   PROMETHEUS    │───────────────▶│   CONTROLLER    │
│  (Metrics DB)   │   PromQL       │ (Decision Logic)│
└─────────────────┘   Queries      └─────────────────┘
         ▲                                    │
         │                                    │ Actuator
         │ Scrape                            │ HTTP API
         │ /metrics                          ▼
┌─────────────────┐                ┌─────────────────┐
│     GO API      │◀───────────────│   SAMPLING      │
│   (Plant)       │  Rate Control  │    CONTROL      │
│                 │                │   (/control/)   │
└─────────────────┘                └─────────────────┘
         │
         │ Telemetry
         ▼ (StatsD, Logs)
┌─────────────────┐
│     VECTOR      │
│ (Data Pipeline) │
└─────────────────┘
```
