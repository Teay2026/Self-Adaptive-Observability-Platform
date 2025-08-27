#!/usr/bin/env python3
import os, time, json, requests
from flask import Flask, request, Response, jsonify
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST

PROM_URL = os.getenv('PROM_URL', 'http://prometheus:9090')
API_URL = os.getenv('API_URL', 'http://go-api:8080')
INTERVAL = int(os.getenv('INTERVAL', '3'))
WINDOW = os.getenv('WINDOW', '30s')
SERVICE = os.getenv('SERVICE', 'api')
ENV = os.getenv('ENV', 'dev')

# Thresholds configurable via env
ERR_HIGH = float(os.getenv('ERR_HIGH', '0.05'))
ERR_LOW  = float(os.getenv('ERR_LOW',  '0.01'))
LAT_HIGH = float(os.getenv('LAT_HIGH', '0.35'))
LAT_LOW  = float(os.getenv('LAT_LOW',  '0.20'))

# Rate bounds/step configurable
MIN_RATE = float(os.getenv('MIN_RATE', '0.1'))
MAX_RATE = float(os.getenv('MAX_RATE', '1.0'))
STEP     = float(os.getenv('STEP',     '0.1'))
COOLDOWN = int(os.getenv('COOLDOWN_SEC', '10'))

app = Flask(__name__)

# Prometheus metrics for controller itself
G_RATE = Gauge('controller_sampling_rate', 'Current sampling rate as seen/applied by controller')
G_LAST_CHANGE = Gauge('controller_last_change_timestamp_seconds', 'Unix timestamp of last sampling change')
C_DECISIONS = Counter('controller_decisions_total', 'Number of decisions taken', ['action', 'src'])


def jlog(event: str, **fields):
    try:
        print(json.dumps({"event": event, **fields}), flush=True)
    except Exception:
        # Fallback to plain printing if serialization fails
        print('LOG', event, fields, flush=True)


def q_err_rate(window: str) -> str:
    return f'sum(rate(api_errors_total[{window}])) / clamp_min(sum(rate(api_requests_total[{window}])), 1e-9)'


def q_p90(window: str) -> str:
    return f'histogram_quantile(0.9, sum(rate(api_request_duration_seconds_bucket[{window}])) by (le))'


def prom_query(q: str):
    try:
        r = requests.get(f"{PROM_URL}/api/v1/query", params={'query': q}, timeout=5)
        r.raise_for_status()
        data = r.json()
        res = data.get('data', {}).get('result', [])
        if not res:
            jlog('prom_query_no_result', query=q)
            return None
        try:
            value = float(res[0]['value'][1])
            jlog('prom_query_success', query=q, value=value)
            return value
        except Exception as e:
            jlog('prom_query_parse_error', query=q, error=str(e))
            return None
    except Exception as e:
        jlog('prom_query_request_error', query=q, error=str(e))
        return None


def adjust(rate: float, up: bool) -> float:
    if up:
        rate = min(MAX_RATE, rate + STEP)
    else:
        rate = max(MIN_RATE, rate - STEP)
    return round(rate, 3)


def get_current_rate() -> float:
    try:
        r = requests.get(f"{API_URL}/control/sampling", timeout=5)
        if r.ok and 'current_rate=' in r.text:
            return float(r.text.strip().split('=')[1])
    except Exception:
        pass
    return MAX_RATE


def set_rate(rate: float):
    try:
        r = requests.get(f"{API_URL}/control/sampling", params={'rate': str(rate)}, timeout=5)
        jlog('set_rate', new_rate=rate, resp_code=r.status_code, resp_text=r.text.strip())
    except Exception as e:
        jlog('set_rate_failed', new_rate=rate, error=str(e))


@app.route('/healthz')
def healthz():
    return 'ok\n'


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/control', methods=['POST'])
def control_from_alert():
    """Webhook Alertmanager: bump sur firing, decay sur resolved_only (avec cooldown)."""
    try:
        payload = request.get_json(force=True, silent=True) or {}
        statuses = [a.get('status') for a in payload.get('alerts', [])]
        firing = any(s == 'firing' for s in statuses)
        resolved_only = statuses and all(s == 'resolved' for s in statuses)
        global last_change_ts, rate
        jlog('ctrl_alert', statuses=statuses)

        now = time.time()
        if firing and (now - last_change_ts >= COOLDOWN):
            nr = adjust(rate, up=True)
            if nr != rate:
                jlog('ctrl_decision', action='bump', src='alert', from_rate=rate, to_rate=nr)
                C_DECISIONS.labels(action='bump', src='alert').inc()
                set_rate(nr)
                rate = nr
                G_RATE.set(rate)
                last_change_ts = now
                G_LAST_CHANGE.set(last_change_ts)
        elif resolved_only and (now - last_change_ts >= COOLDOWN):
            nr = adjust(rate, up=False)
            if nr != rate:
                jlog('ctrl_decision', action='decay', src='alert', from_rate=rate, to_rate=nr)
                C_DECISIONS.labels(action='decay', src='alert').inc()
                set_rate(nr)
                rate = nr
                G_RATE.set(rate)
                last_change_ts = now
                G_LAST_CHANGE.set(last_change_ts)
        return 'ok\n'
    except Exception as e:
        return f'err {e}\n', 500

@app.route('/')
def ui_index():
    # Minimal UI single-page for demo: HTML + vanilla JS
    html = """
<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>Adaptive Controller UI</title>
  <style>
    body{font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;margin:16px;}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;}
    .card{border:1px solid #ddd;border-radius:8px;padding:12px;}
    h2{margin:0 0 8px 0;font-size:1.1rem;}
    button{padding:8px 12px;margin-right:8px}
    input{padding:6px}
    code{background:#f5f5f5;padding:2px 4px;border-radius:4px}
  </style>
</head>
<body>
  <h1>Adaptive Controller — Demo UI</h1>
  <p>Service: <b>__SERVICE__</b> &nbsp; Env: <b>__ENV__</b> &nbsp; Window: <b>__WINDOW__</b> &nbsp; Cooldown: <b>__COOLDOWN__s</b></p>
  <div class=\"grid\">
    <div class=\"card\">
      <h2>État</h2>
      <div>Sampling rate: <b id=\"rate\">…</b></div>
      <div>Err%: <b id=\"err\">…</b> &nbsp; p90(s): <b id=\"p90\">…</b></div>
      <div>Dernière décision: <span id=\"last\">—</span></div>
      <div style=\"margin-top:8px\">
        <button onclick=\"bump()\">Bump +STEP</button>
        <button onclick=\"decay()\">Decay −STEP</button>
        <input id=\"manual\" type=\"number\" min=\"0\" max=\"1\" step=\"0.05\" placeholder=\"0.5\"/>
        <button onclick=\"setManual()\">Fixer</button>
      </div>
    </div>
    <div class=\"card\">
      <h2>Liens</h2>
      <ul>
        <li><a href=\"/metrics\" target=\"_blank\">/metrics (controller)</a></li>
        <li><a href=\"/healthz\" target=\"_blank\">/healthz</a></li>
        <li><a href=\"__PROM_URL__\" target=\"_blank\">Prometheus</a></li>
        <li><a href=\"http://localhost:3000\" target=\"_blank\">Grafana</a></li>
        <li><a href=\"http://localhost:9093\" target=\"_blank\">Alertmanager</a></li>
      </ul>
    </div>
  </div>
  <script>
    async function fetchJSON(u){const r=await fetch(u);return r.json()}
    async function refresh(){
      const s=await fetchJSON('/api/state');
      document.getElementById('rate').textContent=(s.rate!=null? s.rate.toFixed(3) : '—');
      document.getElementById('err').textContent=(s.err==null? '—' : (100*s.err).toFixed(2)+'%');
      document.getElementById('p90').textContent=(s.p90==null? '—' : s.p90.toFixed(3));
      document.getElementById('last').textContent=(s.last || '—');
    }
    async function bump(){await fetch('/api/rate', {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'bump'})}); await refresh()}
    async function decay(){await fetch('/api/rate', {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'decay'})}); await refresh()}
    async function setManual(){const v=parseFloat(document.getElementById('manual').value); if(isNaN(v)) return; await fetch('/api/rate', {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({value:v})}); await refresh()}
    refresh(); setInterval(refresh, 4000);
  </script>
</body>
</html>
"""
    html = (html
            .replace("__SERVICE__", SERVICE)
            .replace("__ENV__", ENV)
            .replace("__WINDOW__", WINDOW)
            .replace("__COOLDOWN__", str(COOLDOWN))
            .replace("__PROM_URL__", PROM_URL))
    return Response(html, mimetype='text/html')

@app.route('/api/state')
def api_state():
    try:
        err = prom_query(q_err_rate(WINDOW))
        p90 = prom_query(q_p90(WINDOW))
        return {'rate': rate, 'err': err, 'p90': p90, 'last': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(last_change_ts)) if last_change_ts else None}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/rate', methods=['POST'])
def api_rate():
    global rate, last_change_ts
    data = request.get_json(force=True, silent=True) or {}
    now = time.time()
    if 'action' in data:
        if now - last_change_ts < COOLDOWN:
            return {'status':'cooldown','seconds_left': int(COOLDOWN - (now - last_change_ts))}, 429
        if data['action'] == 'bump':
            nr = adjust(rate, up=True)
            if nr != rate:
                C_DECISIONS.labels(action='bump', src='manual').inc()
                set_rate(nr)
                rate = nr; G_RATE.set(rate); last_change_ts = now; G_LAST_CHANGE.set(last_change_ts)
        elif data['action'] == 'decay':
            nr = adjust(rate, up=False)
            if nr != rate:
                C_DECISIONS.labels(action='decay', src='manual').inc()
                set_rate(nr)
                rate = nr; G_RATE.set(rate); last_change_ts = now; G_LAST_CHANGE.set(last_change_ts)
        return {'rate': rate}
    if 'value' in data:
        v = float(data['value'])
        v = max(MIN_RATE, min(MAX_RATE, round(v,3)))
        set_rate(v)
        rate = v; G_RATE.set(rate); last_change_ts = now; G_LAST_CHANGE.set(last_change_ts)
        return {'rate': rate}
    return {'error': 'invalid payload'}, 400


if __name__ == '__main__':
    from threading import Thread

    # State
    rate = get_current_rate()
    last_change_ts = 0.0
    G_RATE.set(rate)
    G_LAST_CHANGE.set(last_change_ts)
    jlog('ctrl_start', rate=rate, window=WINDOW,
         thresholds={'err_low': ERR_LOW, 'err_high': ERR_HIGH, 'lat_low': LAT_LOW, 'lat_high': LAT_HIGH},
         step=STEP, cooldown=COOLDOWN, service=SERVICE, env=ENV)

    # Start Flask (webhook + /metrics + /healthz)
    def run_api():
        app.run(host='0.0.0.0', port=8080)

    Thread(target=run_api, daemon=True).start()

    # Polling loop
    while True:
        try:
            err = prom_query(q_err_rate(WINDOW))
            p90 = prom_query(q_p90(WINDOW))
            jlog('ctrl_tick', err=err, p90=p90, rate=rate)
            if err is None or p90 is None or p90 != p90:  # Check for NaN
                time.sleep(INTERVAL)
                continue

            now = time.time()
            # Décision d'augmentation basée sur le taux d'erreur OU la latence
            if (err is not None and err > ERR_HIGH) or (p90 is not None and p90 == p90 and p90 > LAT_HIGH):
                nr = adjust(rate, up=True)
                if nr != rate:
                    jlog('ctrl_decision', action='bump', src='poll', from_rate=rate, to_rate=nr,
                         reason={'err': err, 'p90': p90, 'thr_high': {'err': ERR_HIGH, 'p90': LAT_HIGH}})
                    C_DECISIONS.labels(action='bump', src='poll').inc()
                    set_rate(nr)
                    rate = nr
                    G_RATE.set(rate)
                    last_change_ts = now
                    G_LAST_CHANGE.set(last_change_ts)
            # Décision de diminution basée sur le taux d'erreur ET la latence
            elif (err is not None and err < ERR_LOW) and (p90 is not None and p90 == p90 and p90 < LAT_LOW):
                nr = adjust(rate, up=False)
                if nr != rate:
                    jlog('ctrl_decision', action='decay', src='poll', from_rate=rate, to_rate=nr,
                         reason={'err': err, 'p90': p90, 'thr_low': {'err': ERR_LOW, 'p90': LAT_LOW}})
                    C_DECISIONS.labels(action='decay', src='poll').inc()
                    set_rate(nr)
                    rate = nr
                    G_RATE.set(rate)
                    last_change_ts = now
                    G_LAST_CHANGE.set(last_change_ts)
        except Exception as e:
            jlog('loop_err', error=str(e))
        time.sleep(INTERVAL)

