#!/usr/bin/env python3
import requests
import time
import json
import threading

def generate_high_error_traffic(duration=60):
    """Génère du trafic avec un taux d'erreur élevé pour déclencher l'adaptation"""
    print(f"🚀 Génération de trafic avec erreurs élevées pendant {duration} secondes...")
    
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
                print(f"   - ❌ Requête {request_count}: Erreur {response.status_code}")
            elif request_count % 20 == 0:
                print(f"   - ✅ Requête {request_count}: OK")
            
            # Simuler des erreurs supplémentaires
            if request_count % 3 == 0:  # Erreur toutes les 3 requêtes
                print(f"   - 🚨 Requête {request_count}: Erreur simulée")
                error_count += 1
            
            time.sleep(0.05)  # Plus rapide
            
        except Exception as e:
            error_count += 1
            print(f"   - 💥 Requête {request_count}: Exception {e}")
            time.sleep(0.05)
    
    print(f"🎯 Trafic terminé: {request_count} requêtes, {error_count} erreurs")
    return request_count, error_count

def monitor_controller_adaptation():
    """Surveille l'adaptation du contrôleur en temps réel"""
    print("👀 Surveillance de l'adaptation du contrôleur...")
    
    initial_state = None
    last_rate = None
    adaptation_detected = False
    start_time = time.time()
    
    while not adaptation_detected and (time.time() - start_time) < 120:  # Max 2 minutes
        try:
            response = requests.get('http://localhost:9095/api/state')
            if response.ok:
                state = response.json()
                
                if initial_state is None:
                    initial_state = state
                    print(f"   📊 État initial: rate={state['rate']}, err={state['err']}, p90={state['p90']}")
                
                # Détecter les changements de taux
                if last_rate != state['rate']:
                    if last_rate is not None:
                        print(f"   🔄 ADAPTATION DÉTECTÉE: {last_rate} → {state['rate']}")
                        adaptation_detected = True
                        break
                    last_rate = state['rate']
                
                # Afficher les métriques en temps réel
                if state['err'] is not None:
                    print(f"   📈 Taux d'erreur: {state['err']:.4f}")
                
                if state['p90'] is not None and state['p90'] == state['p90']:  # Not NaN
                    print(f"   ⏱️  Latence p90: {state['p90']:.3f}s")
                
                # Vérifier si on dépasse les seuils
                if state['err'] is not None and state['err'] > 0.05:
                    print(f"   🚨 SEUIL DÉPASSÉ: Taux d'erreur {state['err']:.4f} > 0.05")
                
                if state['p90'] is not None and state['p90'] == state['p90'] and state['p90'] > 0.35:
                    print(f"   🚨 SEUIL DÉPASSÉ: Latence p90 {state['p90']:.3f}s > 0.35s")
                
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Erreur de surveillance: {e}")
            time.sleep(2)
    
    if not adaptation_detected:
        print("   ⏰ Aucune adaptation détectée dans le délai imparti")
    
    return adaptation_detected

def main():
    print("🎯 === TEST FINAL D'ADAPTATION DU SYSTÈME ===\n")
    
    # Vérifier l'état initial
    print("1. 📋 État initial du contrôleur:")
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
    
    # Vérifier les métriques initiales
    print("\n2. 📊 Métriques initiales:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[30s])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (30s): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
        
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_requests_total[30s])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                request_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux de requêtes (30s): {request_rate:.2f} req/s")
            else:
                print("   - Aucun taux de requêtes trouvé")
                
    except Exception as e:
        print(f"   - Erreur lors de la vérification des métriques: {e}")
    
    # Générer du trafic avec erreurs élevées
    print("\n3. 🚀 Génération de trafic avec erreurs élevées...")
    request_count, error_count = generate_high_error_traffic(duration=45)
    
    print(f"\n4. 📈 Résultats du trafic:")
    print(f"   - Total des requêtes: {request_count}")
    print(f"   - Total des erreurs: {error_count}")
    print(f"   - Taux d'erreur: {error_count/request_count*100:.2f}%")
    
    # Attendre que les métriques soient mises à jour
    print("\n5. ⏳ Attente de mise à jour des métriques...")
    time.sleep(15)
    
    # Vérifier les métriques après génération
    print("\n6. 📊 Métriques après génération de trafic:")
    try:
        response = requests.get('http://localhost:9091/api/v1/query?query=rate(api_errors_total[30s])')
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                error_rate = float(data['data']['result'][0]['value'][1])
                print(f"   - Taux d'erreur (30s): {error_rate:.4f}")
            else:
                print("   - Aucun taux d'erreur trouvé")
    except Exception as e:
        print(f"   - Erreur: {e}")
    
    # Surveiller l'adaptation
    print("\n7. 👀 Surveillance de l'adaptation du contrôleur...")
    adaptation_detected = monitor_controller_adaptation()
    
    # État final
    print("\n8. 🎯 État final:")
    try:
        response = requests.get('http://localhost:9095/api/state')
        if response.ok:
            state = response.json()
            print(f"   - Taux de sampling final: {state['rate']}")
            print(f"   - Taux d'erreur final: {state['err']}")
            print(f"   - Latence p90 finale: {state['p90']}")
            
            if adaptation_detected:
                print(f"   - 🎉 SUCCÈS: Le contrôleur s'est adapté!")
            else:
                print(f"   - ⚠️  Le contrôleur n'a pas détecté d'adaptation")
                
        else:
            print(f"   - Erreur: {response.status_code}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    print("\n🎯 === TEST TERMINÉ ===")

if __name__ == "__main__":
    main() 