#!/usr/bin/env python3
import requests
import time
import json
import socket

def send_statsd(metric):
    """Envoie une métrique StatsD via UDP"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(metric.encode(), ('localhost', 8125))
    sock.close()

def generate_traffic(duration=60, interval=0.1):
    """Génère du trafic pour tester le système"""
    print(f"Génération de trafic pendant {duration} secondes...")
    
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration:
        try:
            # Appel à l'API Go
            response = requests.get('http://localhost:8080/', timeout=1)
            request_count += 1
            
            # Envoyer des métriques StatsD
            send_statsd(f"api.requests:1|c|#service:api,env:dev")
            
            if response.status_code >= 500:
                send_statsd(f"api.errors:1|c|#service:api,env:dev")
            
            # Simuler une latence variable
            latency = 50 + (request_count % 100)  # 50-150ms
            send_statsd(f"api.request_duration_ms:{latency}|ms|#service:api,env:dev")
            
            if request_count % 10 == 0:
                print(f"Requêtes envoyées: {request_count}")
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"Erreur lors de la requête: {e}")
            time.sleep(interval)
    
    print(f"Test terminé. Total des requêtes: {request_count}")

def check_controller_state():
    """Vérifie l'état du contrôleur"""
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"État du contrôleur: {json.dumps(state, indent=2)}")
            return state
        else:
            print(f"Erreur lors de la vérification de l'état: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur de connexion au contrôleur: {e}")
        return None

def check_metrics():
    """Vérifie les métriques dans Prometheus"""
    try:
        # Vérifier le taux d'erreur
        error_query = 'sum(rate(api_errors{service="api",env="dev"}[1m])) / clamp_min(sum(rate(api_requests{service="api",env="dev"}[1m])), 1e-9)'
        response = requests.get('http://localhost:9091/api/v1/query', params={'query': error_query})
        
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"Taux d'erreur actuel: {error_rate:.4f}")
            else:
                print("Aucune métrique d'erreur trouvée")
        
        # Vérifier la latence p90
        latency_query = 'histogram_quantile(0.9, sum(rate(api_request_duration_ms_bucket[1m])) by (le))'
        response = requests.get('http://localhost:9091/api/v1/query', params={'query': latency_query})
        
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                p90_latency = float(data['data']['result'][0]['value'][1])
                print(f"Latence p90 actuelle: {p90_latency:.3f}s")
            else:
                print("Aucune métrique de latence trouvée")
                
    except Exception as e:
        print(f"Erreur lors de la vérification des métriques: {e}")

def main():
    print("=== Test du système d'observabilité adaptative ===\n")
    
    # Vérifier l'état initial
    print("1. État initial du contrôleur:")
    initial_state = check_controller_state()
    
    print("\n2. Métriques initiales:")
    check_metrics()
    
    print("\n3. Génération de trafic...")
    generate_traffic(duration=30, interval=0.2)
    
    print("\n4. État après génération de trafic:")
    final_state = check_controller_state()
    
    print("\n5. Métriques finales:")
    check_metrics()
    
    if initial_state and final_state:
        if final_state['rate'] != initial_state['rate']:
            print(f"\n✅ SUCCÈS: Le contrôleur a ajusté le taux de sampling de {initial_state['rate']} à {final_state['rate']}")
        else:
            print(f"\n⚠️  Le contrôleur n'a pas changé le taux de sampling (toujours {final_state['rate']})")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    main() 