#!/usr/bin/env python3
import requests
import time
import json

def generate_errors():
    """Génère des erreurs pour tester le système d'adaptation"""
    print("=== Test de génération d'erreurs ===\n")
    
    # Vérifier l'état initial
    print("1. État initial du contrôleur:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling: {state['rate']}")
            print(f"   - Taux d'erreur: {state['err']}")
            print(f"   - Latence p90: {state['p90']}")
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    # Générer des erreurs en appelant un endpoint inexistant
    print("\n2. Génération d'erreurs...")
    error_count = 0
    for i in range(30):
        try:
            # Appeler un endpoint qui n'existe pas pour générer des erreurs 404
            response = requests.get('http://localhost:8080/error', timeout=1)
            if response.status_code >= 400:
                error_count += 1
                print(f"   - Requête {i+1}: Erreur {response.status_code}")
            else:
                print(f"   - Requête {i+1}: OK")
        except Exception as e:
            error_count += 1
            print(f"   - Requête {i+1}: Exception {e}")
        time.sleep(0.1)
    
    print(f"\n   Total des erreurs générées: {error_count}")
    
    # Attendre que les métriques soient mises à jour
    print("\n3. Attente de mise à jour des métriques...")
    time.sleep(10)
    
    # Vérifier l'état final
    print("\n4. État final du contrôleur:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling: {state['rate']}")
            print(f"   - Taux d'erreur: {state['err']}")
            print(f"   - Latence p90: {state['p90']}")
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    # Vérifier les métriques d'erreur
    print("\n5. Métriques d'erreur:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[1m])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (1m): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
    except Exception as e:
        print(f"   - Erreur: {e}")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    generate_errors() 