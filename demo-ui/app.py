#!/usr/bin/env python3
"""
Interface de démonstration unifiée pour la plateforme d'observabilité auto-adaptative
Cette interface s'intègre parfaitement avec l'architecture existante et utilise les endpoints
déjà disponibles dans le contrôleur et l'API.
"""

import os
import json
import requests
import time
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import subprocess
import threading
from requests.models import Response

app = Flask(__name__)

# Configuration basée sur l'architecture existante
# Utilisation des noms de services Docker pour les connexions internes
SERVICES = {
    'go-api': 'http://go-api:8080',
    'prometheus': 'http://prometheus:9090',
    'alertmanager': 'http://alertmanager:9093',
    'controller': 'http://controller:8080',
    'grafana': 'http://grafana:3000',
    'vector': 'http://vector:9090'
}

# URLs externes pour l'interface utilisateur
EXTERNAL_URLS = {
    'go-api': 'http://localhost:8080',
    'prometheus': 'http://localhost:9091',
    'alertmanager': 'http://localhost:9093',
    'controller': 'http://localhost:9095',
    'grafana': 'http://localhost:3000',
    'vector': 'http://localhost:9090'
}

class ServiceMonitor:
    """Moniteur des services basé sur l'architecture existante"""
    
    def __init__(self):
        self.status = {}
        self.last_check = {}
    
    def check_service(self, service_name, url):
        """Vérifie le statut d'un service"""
        try:
            start_time = time.time()
            
            # Endpoints spécifiques pour chaque service
            if service_name == 'go-api':
                response = requests.get(f"{url}/healthz", timeout=5)
            elif service_name == 'controller':
                response = requests.get(f"{url}/healthz", timeout=5)
            elif service_name == 'prometheus':
                response = requests.get(f"{url}/api/v1/query?query=up", timeout=5)
            elif service_name == 'alertmanager':
                response = requests.get(f"{url}/-/healthy", timeout=5)
            elif service_name == 'vector':
                # Vector n'a pas d'endpoint de santé simple, testons juste la connectivité
                try:
                    requests.get(f"{url}/", timeout=5)
                    # Vector répond, on crée une réponse simulée avec 200
                    class MockResponse:
                        def __init__(self):
                            self.status_code = 200
                    response = MockResponse()
                except Exception as e:
                    raise e
            else:
                response = requests.get(url, timeout=5)
            
            response_time = time.time() - start_time
            
            self.status[service_name] = {
                'status': 'healthy' if response.status_code < 400 else 'unhealthy',
                'response_time': round(response_time * 1000, 2),
                'status_code': response.status_code,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            self.status[service_name] = {
                'status': 'down',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def check_all_services(self):
        """Vérifie tous les services"""
        for service_name, url in SERVICES.items():
            self.check_service(service_name, url)
        return self.status

monitor = ServiceMonitor()

class LoadGenerator:
    """Générateur de charge utilisant le script existant"""
    
    @staticmethod
    def generate_load(duration=60, concurrency=4, url="http://localhost:8080/"):
        """Génère de la charge en utilisant le script loadgen.sh existant"""
        try:
            # Utiliser le script existant
            script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'loadgen.sh')
            if not os.path.exists(script_path):
                return False, "Script loadgen.sh non trouvé"
            
            # Rendre le script exécutable
            os.chmod(script_path, 0o755)
            
            # Lancer le script en arrière-plan
            cmd = [script_path, url, str(duration), str(concurrency)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True, f"Génération de charge démarrée: {duration}s, {concurrency} connexions"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

@app.route('/')
def index():
    """Page principale de démonstration"""
    return render_template('dashboard.html')

@app.route('/demo')
def demo():
    """Page de démonstration originale"""
    return render_template('demo.html')

@app.route('/api/health')
def health():
    """Endpoint de santé de l'interface de démonstration"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'demo-ui'
    })

@app.route('/api/status')
def get_status():
    """Statut de tous les services"""
    return jsonify(monitor.check_all_services())

@app.route('/api/controller/state')
def controller_state():
    """État du contrôleur via son API existante"""
    try:
        response = requests.get(f"{SERVICES['controller']}/api/state", timeout=5)
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Erreur {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/controller/rate', methods=['POST'])
def controller_rate():
    """Contrôle du taux via l'API du contrôleur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        
        # Utiliser l'API du contrôleur existante
        response = requests.post(f"{SERVICES['controller']}/api/rate", 
                               json=data, timeout=5)
        
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Erreur {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/api/sampling')
def get_sampling():
    """Taux d'échantillonnage via l'API Go existante"""
    try:
        response = requests.get(f"{SERVICES['go-api']}/control/sampling", timeout=5)
        if response.ok:
            return jsonify({
                'sampling_rate': response.text.strip(),
                'status': 'success'
            })
        else:
            return jsonify({'error': f'Erreur {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/api/sampling', methods=['POST'])
def set_sampling():
    """Modification du taux d'échantillonnage via l'API Go existante"""
    try:
        data = request.get_json()
        if not data or 'rate' not in data:
            return jsonify({'error': 'Taux manquant'}), 400
        
        rate = data['rate']
        response = requests.get(f"{SERVICES['go-api']}/control/sampling", 
                              params={'rate': str(rate)}, timeout=5)
        
        if response.ok:
            return jsonify({
                'success': True,
                'new_rate': rate,
                'response': response.text.strip()
            })
        else:
            return jsonify({'error': f'Erreur {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prometheus/query')
def prometheus_query():
    """Requêtes Prometheus via l'API existante"""
    try:
        query = request.args.get('query', 'up')
        response = requests.get(f"{SERVICES['prometheus']}/api/v1/query", 
                              params={'query': query}, timeout=10)
        
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Erreur {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load', methods=['POST'])
def generate_load():
    """Génération de charge via le script existant"""
    try:
        data = request.get_json()
        duration = data.get('duration', 60)
        concurrency = data.get('concurrency', 4)
        url = data.get('url', 'http://localhost:8080/')
        
        success, message = LoadGenerator.generate_load(duration, concurrency, url)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'url': url,
                'duration': duration,
                'concurrency': concurrency
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/metrics/summary')
def metrics_summary():
    """Résumé des métriques principales"""
    try:
        metrics = {}
        
        # Taux de requêtes
        response = requests.get(f"{SERVICES['prometheus']}/api/v1/query", 
                              params={'query': 'rate(api_requests_total[1m])'}, timeout=5)
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                metrics['requests_per_sec'] = float(data['data']['result'][0]['value'][1])
        
        # Total requests
        response = requests.get(f"{SERVICES['prometheus']}/api/v1/query", 
                              params={'query': 'api_requests_total'}, timeout=5)
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                metrics['total_requests'] = int(float(data['data']['result'][0]['value'][1]))
        
        # Taux d'erreur
        response = requests.get(f"{SERVICES['prometheus']}/api/v1/query", 
                              params={'query': 'rate(api_errors_total[1m]) / clamp_min(rate(api_requests_total[1m]), 1e-9) * 100'}, timeout=5)
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                metrics['error_rate_percent'] = float(data['data']['result'][0]['value'][1])
            else:
                metrics['error_rate_percent'] = 0.0
        
        # Latence P90
        response = requests.get(f"{SERVICES['prometheus']}/api/v1/query", 
                              params={'query': 'histogram_quantile(0.9, rate(api_request_duration_seconds_bucket[1m])) * 1000'}, timeout=5)
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('result'):
                metrics['latency_p90_ms'] = float(data['data']['result'][0]['value'][1])
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grafana/dashboards')
def grafana_dashboards():
    """Liste des dashboards Grafana disponibles"""
    dashboards = [
        {
            'name': 'API Observability',
            'url': f"{SERVICES['grafana']}/d/api-observability",
            'description': 'Métriques principales de l\'API'
        },
        {
            'name': 'Controller',
            'url': f"{SERVICES['grafana']}/d/controller",
            'description': 'Métriques du contrôleur auto-adaptatif'
        },
        {
            'name': 'Vector Overview',
            'url': f"{SERVICES['grafana']}/d/vector-overview",
            'description': 'Vue d\'ensemble de Vector'
        }
    ]
    return jsonify(dashboards)

if __name__ == '__main__':
    # Port différent pour éviter les conflits
    app.run(host='0.0.0.0', port=8081, debug=True)
