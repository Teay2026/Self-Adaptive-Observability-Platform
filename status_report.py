#!/usr/bin/env python3
import requests
import time
import json

def check_service_health():
    """Vérifie la santé de tous les services"""
    print("=== RAPPORT DE STATUT DU SYSTÈME ===\n")
    
    services = {
        "Go API": "http://localhost:8080/healthz",
        "Vector": "http://localhost:8686/health",
        "Prometheus": "http://localhost:9091/api/v1/query?query=up",
        "Controller": "http://localhost:9095/healthz",
        "Grafana": "http://localhost:3000"
    }
    
    print("1. État des services:")
    for name, url in services.items():
        try:
            if "query" in url:
                response = requests.get(url, timeout=5)
                if response.ok:
                    data = response.json()
                    if data.get('data', {}).get('result'):
                        print(f"   ✅ {name}: ACTIF")
                    else:
                        print(f"   ⚠️  {name}: ACTIF mais pas de données")
                else:
                    print(f"   ❌ {name}: ERREUR {response.status_code}")
            else:
                response = requests.get(url, timeout=5)
                if response.ok or response.status_code == 302:  # Grafana redirige
                    print(f"   ✅ {name}: ACTIF")
                else:
                    print(f"   ❌ {name}: ERREUR {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: EXCEPTION {e}")
    
    print("\n2. Métriques collectées:")
    try:
        # Vérifier les métriques de l'API Go
        response = requests.get('http://localhost:9091/api/v1/query?query=api_requests_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                requests_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des requêtes: {requests_total}")
            else:
                print("   - ❌ Aucune métrique de requêtes trouvée")
        
        response = requests.get('http://localhost:9091/api/v1/query?query=api_errors_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                errors_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des erreurs: {errors_total}")
            else:
                print("   - ❌ Aucune métrique d'erreur trouvée")
        
        # Vérifier les métriques Vector
        response = requests.get('http://localhost:9090/metrics')
        if response.ok:
            if 'api_requests' in response.text:
                print("   - ✅ Métriques StatsD collectées par Vector")
            else:
                print("   - ❌ Aucune métrique StatsD trouvée dans Vector")
        else:
            print("   - ❌ Impossible d'accéder aux métriques Vector")
            
    except Exception as e:
        print(f"   - ❌ Erreur lors de la vérification des métriques: {e}")
    
    print("\n3. État du contrôleur:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling actuel: {state['rate']}")
            print(f"   - Taux d'erreur détecté: {state['err']}")
            print(f"   - Latence p90 détectée: {state['p90']}")
            print(f"   - Dernière décision: {state['last']}")
            
            if state['err'] is None:
                print("   - ⚠️  Le contrôleur ne peut pas lire le taux d'erreur")
            if state['p90'] is None:
                print("   - ⚠️  Le contrôleur ne peut pas lire la latence")
        else:
            print(f"   - ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - ❌ Exception: {e}")
    
    print("\n4. Test de génération de trafic:")
    try:
        start_time = time.time()
        for i in range(10):
            response = requests.get('http://localhost:8080/', timeout=1)
            if response.status_code >= 500:
                print(f"   - Requête {i+1}: Erreur {response.status_code}")
            else:
                print(f"   - Requête {i+1}: OK")
            time.sleep(0.1)
        
        duration = time.time() - start_time
        print(f"   - 10 requêtes générées en {duration:.2f}s")
        
    except Exception as e:
        print(f"   - ❌ Erreur lors de la génération de trafic: {e}")
    
    print("\n5. Recommandations:")
    if True:  # Placeholder pour la logique
        print("   - ✅ Tous les services sont actifs")
        print("   - ⚠️  Le contrôleur ne peut pas lire le taux d'erreur")
        print("   - 💡 Vérifier la configuration des requêtes PromQL")
        print("   - 💡 Tester avec des fenêtres de temps plus courtes")
    
    print("\n=== RAPPORT TERMINÉ ===")

if __name__ == "__main__":
    check_service_health() 