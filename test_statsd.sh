#!/bin/bash
# Script de test pour StatsD

echo "Test d'envoi de métriques StatsD..."

# Envoyer une métrique counter
echo "api.requests:1|c|#service:api,env:dev" | socat - UDP:localhost:8125
echo "Métrique counter envoyée"

# Envoyer une métrique timing
echo "api.request_duration_ms:150|ms|#service:api,env:dev" | socat - UDP:localhost:8125
echo "Métrique timing envoyée"

# Envoyer une métrique gauge
echo "api.active_connections:5|g|#service:api,env:dev" | socat - UDP:localhost:8125
echo "Métrique gauge envoyée"

echo "Test terminé" 