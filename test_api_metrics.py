#!/usr/bin/env python3
import requests
import time
import json

def test_api_metrics():
    """Test des métriques de l'API Go via Prometheus"""
    print("=== Test des métriques de l'API Go ===\n")
    
    # Vérifier les métriques initiales
    print("1. Métriques initiales:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=api_requests_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                requests_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des requêtes: {requests_total}")
            else:
                print("   - Aucune métrique de requêtes trouvée")
        
        response = requests.get('http://localhost:9091/api/v1/query?query=api_errors_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                errors_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des erreurs: {errors_total}")
            else:
                print("   - Aucune métrique d'erreur trouvée")
    except Exception as e:
        print(f"   - Erreur lors de la vérification des métriques: {e}")
    
    # Générer du trafic
    print("\n2. Génération de trafic...")
    for i in range(20):
        try:
            response = requests.get('http://localhost:8080/', timeout=1)
            if response.status_code >= 500:
                print(f"   - Requête {i+1}: Erreur {response.status_code}")
            else:
                print(f"   - Requête {i+1}: OK")
        except Exception as e:
            print(f"   - Requête {i+1}: Exception {e}")
        time.sleep(0.1)
    
    # Attendre que les métriques soient mises à jour
    print("\n3. Attente de mise à jour des métriques...")
    time.sleep(5)
    
    # Vérifier les métriques finales
    print("\n4. Métriques finales:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=api_requests_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                requests_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des requêtes: {requests_total}")
            else:
                print("   - Aucune métrique de requêtes trouvée")
        
        response = requests.get('http://localhost:9091/api/v1/query?query=api_errors_total')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                errors_total = float(data['data']['result'][0]['value'][1])
                print(f"   - Total des erreurs: {errors_total}")
            else:
                print("   - Aucune métrique d'erreur trouvée")
        
        # Vérifier le taux d'erreur
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[1m])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (1m): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
                
    except Exception as e:
        print(f"   - Erreur lors de la vérification des métriques: {e}")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    test_api_metrics() 