#!/usr/bin/env python3
import requests
import time
import json
import threading

def generate_continuous_traffic(duration=60):
    """Génère du trafic continu pour tester l'adaptation"""
    print(f"Génération de trafic continu pendant {duration} secondes...")
    
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

def monitor_controller():
    """Surveille l'état du contrôleur"""
    print("Surveillance du contrôleur...")
    
    initial_state = None
    last_rate = None
    
    while True:
        try:
            response = requests.get('http://localhost:9095/api/state')
            if response.ok:
                state = response.json()
                
                if initial_state is None:
                    initial_state = state
                    print(f"   - État initial: rate={state['rate']}, err={state['err']}, p90={state['p90']}")
                
                if last_rate != state['rate']:
                    print(f"   - 🔄 Changement de taux: {last_rate} → {state['rate']}")
                    last_rate = state['rate']
                
                if state['err'] is not None:
                    print(f"   - 📊 Taux d'erreur détecté: {state['err']:.4f}")
                
                if state['p90'] is not None:
                    print(f"   - ⏱️  Latence p90: {state['p90']:.3f}s")
                
            time.sleep(5)
            
        except Exception as e:
            print(f"   - ❌ Erreur de surveillance: {e}")
            time.sleep(5)

def main():
    print("=== TEST FINAL DU SYSTÈME D'ADAPTATION ===\n")
    
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
    monitor_thread = threading.Thread(target=monitor_controller, daemon=True)
    monitor_thread.start()
    
    print("\n3. Génération de trafic continu...")
    time.sleep(2)  # Laisser le temps à la surveillance de démarrer
    
    # Générer du trafic
    request_count, error_count = generate_continuous_traffic(duration=45)
    
    print(f"\n4. Résultats du test:")
    print(f"   - Total des requêtes: {request_count}")
    print(f"   - Total des erreurs: {error_count}")
    print(f"   - Taux d'erreur: {error_count/request_count*100:.2f}%")
    
    # Vérifier l'état final
    print("\n5. État final du contrôleur:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling final: {state['rate']}")
            print(f"   - Taux d'erreur final: {state['err']}")
            print(f"   - Latence p90 finale: {state['p90']}")
            
            if state['rate'] != 1.0:
                print(f"   - ✅ SUCCÈS: Le contrôleur s'est adapté!")
            else:
                print(f"   - ⚠️  Le contrôleur n'a pas changé le taux de sampling")
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    print("\n=== TEST TERMINÉ ===")

if __name__ == "__main__":
    main() 