#!/usr/bin/env python3
import requests
import time
import json
import threading

def continuous_traffic_generator():
    """Génère du trafic continu pour maintenir les métriques actives"""
    print("Génération de trafic continu en arrière-plan...")
    
    while True:
        try:
            # Appeler l'API Go
            response = requests.get('http://localhost:8080/', timeout=1)
            
            # Simuler des erreurs occasionnelles
            if time.time() % 10 < 2:  # Erreur toutes les 10 secondes
                print("   - Génération d'erreur simulée")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   - Erreur de génération: {e}")
            time.sleep(0.5)

def test_controller_adaptation():
    """Teste l'adaptation du contrôleur avec du trafic continu"""
    print("=== TEST D'ADAPTATION DU CONTRÔLEUR ===\n")
    
    # Démarrer le générateur de trafic en arrière-plan
    print("1. Démarrage du générateur de trafic continu...")
    traffic_thread = threading.Thread(target=continuous_traffic_generator, daemon=True)
    traffic_thread.start()
    
    # Attendre que les métriques soient actives
    print("2. Attente de l'activation des métriques...")
    time.sleep(15)
    
    # Vérifier l'état initial
    print("3. État initial du contrôleur:")
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
    
    # Vérifier les métriques en temps réel
    print("\n4. Vérification des métriques:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[1m])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (1m): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
        
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
    
    # Surveiller l'adaptation
    print("\n5. Surveillance de l'adaptation (30 secondes)...")
    start_time = time.time()
    initial_rate = None
    
    while time.time() - start_time < 30:
        try:
            response = requests.get('http://localhost:9095/api/state')
            if response.ok:
                state = response.json()
                
                if initial_rate is None:
                    initial_rate = state['rate']
                    print(f"   - Taux initial: {initial_rate}")
                
                if state['rate'] != initial_rate:
                    print(f"   - 🔄 ADAPTATION DÉTECTÉE: {initial_rate} → {state['rate']}")
                    break
                
                if state['err'] is not None:
                    print(f"   - 📊 Taux d'erreur détecté: {state['err']:.4f}")
                
                if state['p90'] is not None:
                    print(f"   - ⏱️  Latence p90: {state['p90']:.3f}s")
                
            time.sleep(3)
            
        except Exception as e:
            print(f"   - Erreur de surveillance: {e}")
            time.sleep(3)
    
    # État final
    print("\n6. État final:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling final: {state['rate']}")
            print(f"   - Taux d'erreur final: {state['err']}")
            print(f"   - Latence p90 finale: {state['p90']}")
            
            if state['rate'] != initial_rate:
                print(f"   - ✅ SUCCÈS: Le contrôleur s'est adapté!")
            else:
                print(f"   - ⚠️  Le contrôleur n'a pas changé le taux de sampling")
                
            if state['err'] is not None:
                print(f"   - ✅ SUCCÈS: Le contrôleur peut lire le taux d'erreur!")
            else:
                print(f"   - ❌ Le contrôleur ne peut pas lire le taux d'erreur")
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    print("\n=== TEST TERMINÉ ===")

if __name__ == "__main__":
    test_controller_adaptation() 