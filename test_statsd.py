#!/usr/bin/env python3
import socket
import time

def send_statsd(metric):
    """Envoie une métrique StatsD via UDP"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(metric.encode(), ('localhost', 8125))
    sock.close()
    print(f"Envoyé: {metric}")

def main():
    print("Test d'envoi de métriques StatsD...")
    
    # Métrique counter
    send_statsd("api.requests:1|c|#service:api,env:dev")
    
    # Métrique timing
    send_statsd("api.request_duration_ms:150|ms|#service:api,env:dev")
    
    # Métrique gauge
    send_statsd("api.active_connections:5|g|#service:api,env:dev")
    
    print("Test terminé")

if __name__ == "__main__":
    main() 