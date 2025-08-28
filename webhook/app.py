#!/usr/bin/env python3
"""
Simple webhook service for AlertManager notifications
Logs all incoming webhook calls for debugging and monitoring
"""

import json
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    """Handle webhook calls from AlertManager"""
    try:
        if request.method == 'POST':
            data = request.get_json(force=True, silent=True) or {}
            timestamp = datetime.now().isoformat()
            
            # Log the webhook call
            log_entry = {
                'timestamp': timestamp,
                'method': 'POST',
                'headers': dict(request.headers),
                'data': data
            }
            
            print(json.dumps(log_entry), flush=True)
            
            # Extract alert information if available
            alerts = data.get('alerts', [])
            if alerts:
                for alert in alerts:
                    alert_log = {
                        'timestamp': timestamp,
                        'alert_name': alert.get('labels', {}).get('alertname', 'unknown'),
                        'status': alert.get('status', 'unknown'),
                        'severity': alert.get('labels', {}).get('severity', 'unknown'),
                        'summary': alert.get('annotations', {}).get('summary', ''),
                        'description': alert.get('annotations', {}).get('description', '')
                    }
                    print(f"ALERT: {json.dumps(alert_log)}", flush=True)
            
            return jsonify({'status': 'received', 'timestamp': timestamp})
        
        else:  # GET request
            return jsonify({
                'status': 'healthy',
                'service': 'webhook',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        error_log = {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'method': request.method
        }
        print(f"ERROR: {json.dumps(error_log)}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting webhook service on port 8080", flush=True)
    app.run(host='0.0.0.0', port=8080, debug=False)
