#!/usr/bin/env python3
import requests
import time
import json
import threading

def generate_traffic_with_errors(duration=60):
    """Génère du trafic avec des erreurs pour tester l'adaptation"""
    print(f"Génération de trafic avec erreurs pendant {duration} secondes...")
    
    start_time = time.time()
    request_count = 0
    error_count = 0
    
    while time.time() - start_time < duration:
        try:
            # Appeler l'API Go
            response = requests.get('http://localhost:8080/', timeout=1)
            request_count += 1
            
            if response.status_code >= 500:
                error_count += 1
                print(f"   - Requête {request_count}: Erreur {response.status_code}")
            elif request_count % 20 == 0:
                print(f"   - Requête {request_count}: OK")
            
            time.sleep(0.1)
            
        except Exception as e:
            error_count += 1
            print(f"   - Requête {request_count}: Exception {e}")
            time.sleep(0.1)
    
    print(f"Trafic terminé: {request_count} requêtes, {error_count} erreurs")
    return request_count, error_count

def monitor_controller_state():
    """Surveille l'état du contrôleur en temps réel"""
    print("Surveillance du contrôleur en temps réel...")
    
    initial_state = None
    last_rate = None
    last_change = None
    
    while True:
        try:
            response = requests.get('http://localhost:9095/api/state')
            if response.ok:
                state = response.json()
                
                if initial_state is None:
                    initial_state = state
                    print(f"   - État initial: rate={state['rate']}, err={state['err']}, p90={state['p90']}")
                
                # Détecter les changements de taux
                if last_rate != state['rate']:
                    if last_rate is not None:
                        print(f"   - 🔄 CHANGEMENT DÉTECTÉ: {last_rate} → {state['rate']}")
                    last_rate = state['rate']
                
                # Afficher les métriques en temps réel
                if state['err'] is not None:
                    print(f"   - 📊 Taux d'erreur: {state['err']:.4f}")
                
                if state['p90'] is not None:
                    print(f"   - ⏱️  Latence p90: {state['p90']:.3f}s")
                
                # Afficher la dernière décision
                if state['last'] != last_change:
                    if state['last'] is not None:
                        print(f"   - 📝 Dernière décision: {state['last']}")
                    last_change = state['last']
                
            time.sleep(3)
            
        except Exception as e:
            print(f"   - ❌ Erreur de surveillance: {e}")
            time.sleep(3)

def check_metrics_realtime():
    """Vérifie les métriques en temps réel"""
    print("\nVérification des métriques en temps réel:")
    
    try:
        # Vérifier le taux d'erreur
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[1m])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (1m): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
        
        # Vérifier le taux de requêtes
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_requests_total[1m])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                request_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux de requêtes (1m): {request_rate:.2f} req/s")
            else:
                print("   - Aucun taux de requêtes trouvé")
                
    except Exception as e:
        print(f"   - Erreur lors de la vérification des métriques: {e}")

def main():
    print("=== TEST DU SYSTÈME CORRIGÉ ===\n")
    
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
    
    print("\n2. Démarrage de la surveillance du contrôleur...")
    monitor_thread = threading.Thread(target=monitor_controller_state, daemon=True)
    monitor_thread.start()
    
    print("\n3. Vérification des métriques initiales...")
    check_metrics_realtime()
    
    print("\n4. Génération de trafic avec erreurs...")
    time.sleep(2)  # Laisser le temps à la surveillance de démarrer
    
    # Générer du trafic
    request_count, error_count = generate_traffic_with_errors(duration=45)
    
    print(f"\n5. Résultats du test:")
    print(f"   - Total des requêtes: {request_count}")
    print(f"   - Total des erreurs: {error_count}")
    print(f"   - Taux d'erreur: {error_count/request_count*100:.2f}%")
    
    # Attendre un peu plus pour voir l'adaptation
    print("\n6. Attente de l'adaptation du contrôleur...")
    time.sleep(20)
    
    # Vérifier l'état final
    print("\n7. État final du contrôleur:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling final: {state['rate']}")
            print(f"   - Taux d'erreur final: {state['err']}")
            print(f"   - Latence p90 finale: {state['p90']}")
            
            if state['rate'] != 1.0:
                print(f"   - ✅ SUCCÈS: Le contrôleur s'est adapté de 1.0 à {state['rate']}!")
            else:
                print(f"   - ⚠️  Le contrôleur n'a pas changé le taux de sampling")
                
            if state['err'] is not None:
                print(f"   - ✅ SUCCÈS: Le contrôleur peut maintenant lire le taux d'erreur!")
            else:
                print(f"   - ❌ Le contrôleur ne peut toujours pas lire le taux d'erreur")
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    print("\n8. Métriques finales:")
    check_metrics_realtime()
    
    print("\n=== TEST TERMINÉ ===")

if __name__ == "__main__":
    main() 