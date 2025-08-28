SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help up down restart demo urls logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Build and start the stack
	docker compose up -d --build

down: ## Stop the stack
	docker compose down

restart: ## Restart the stack
	docker compose restart

urls: ## Print service URLs
	@echo "API:           http://localhost:8080" 
	@echo "Prometheus:    http://localhost:9091" 
	@echo "Alertmanager:  http://localhost:9093" 
	@echo "Controller:    http://localhost:9095/healthz (and /metrics)" 
	@echo "Grafana:       http://localhost:3000 (admin/admin)"
	@echo "Demo UI:       http://localhost:8081"

logs: ## Follow controller logs
	docker compose logs -f controller

.demo-check:
	@command -v curl >/dev/null || (echo "curl required" && exit 1)
	@chmod +x scripts/loadgen.sh

load: .demo-check ## Generate load for 60s (override DURATION=.. CONCURRENCY=.. URL=..)
	DURATION=$${DURATION:-60} CONCURRENCY=$${CONCURRENCY:-4} URL=$${URL:-http://localhost:8080/} ./scripts/loadgen.sh $$URL $$DURATION $$CONCURRENCY

demo: up urls ## Run a simple demo: start, print URLs, generate load
	$(MAKE) load DURATION=90 CONCURRENCY=6
	$(MAKE) logs

demo-ui: ## Start only the demo UI for testing
	cd demo-ui && python app.py

test-demo: ## Test the demo UI endpoints
	curl -s http://localhost:8081/api/health | jq .
	curl -s http://localhost:8081/api/status | jq .

demo: ## Run the complete interactive demo
	python demo_platform.py

