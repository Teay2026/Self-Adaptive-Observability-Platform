#!/usr/bin/env python3
import os, time, json, requests
from flask import Flask, request

PROM_URL = os.getenv('PROM_URL', 'http://prometheus:9090')
API_URL = os.getenv('API_URL', 'http://go-api:8080')
INTERVAL = int(os.getenv('INTERVAL', '10'))
WINDOW = os.getenv('WINDOW', '2m')
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
COOLDOWN = int(os.getenv('COOLDOWN_SEC', '30'))

app = Flask(__name__)


def jlog(event: str, **fields):
    try:
        print(json.dumps({"event": event, **fields}), flush=True)
    except Exception:
        # Fallback to plain printing if serialization fails
        print('LOG', event, fields, flush=True)


def q_err_rate(window: str) -> str:
    return f'sum(rate(api__errors{{service="{SERVICE}",env="{ENV}"}}[{window}])) / clamp_min(sum(rate(api__requests{{service="{SERVICE}",env="{ENV}"}}[{window}])), 1e-9)'


def q_p90(window: str) -> str:
    return f'histogram_quantile(0.9, sum(rate(api_request_duration_seconds_bucket[{window}])) by (le))'


def prom_query(q: str):
    r = requests.get(f"{PROM_URL}/api/v1/query", params={'query': q}, timeout=5)
    r.raise_for_status()
    data = r.json()
    res = data.get('data', {}).get('result', [])
    if not res:
        return None
    try:
        return float(res[0]['value'][1])
    except Exception:
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


@app.route('/control', methods=['POST'])
def control_from_alert():
    """Optional webhook to drive changes from Alertmanager if we later route here."""
    try:
        payload = request.get_json(force=True, silent=True) or {}
        # Basic policy: bump on any firing, decay on all resolved
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
                set_rate(nr)
                rate = nr
                last_change_ts = now
        elif resolved_only and (now - last_change_ts >= COOLDOWN):
            nr = adjust(rate, up=False)
            if nr != rate:
                jlog('ctrl_decision', action='decay', src='alert', from_rate=rate, to_rate=nr)
                set_rate(nr)
                rate = nr
                last_change_ts = now
        return 'ok\n'
    except Exception as e:
        return f'err {e}\n', 500


if __name__ == '__main__':
    from threading import Thread

    # State
    rate = get_current_rate()
    last_change_ts = 0.0
    jlog('ctrl_start', rate=rate, window=WINDOW,
         thresholds={'err_low': ERR_LOW, 'err_high': ERR_HIGH, 'lat_low': LAT_LOW, 'lat_high': LAT_HIGH},
         step=STEP, cooldown=COOLDOWN, service=SERVICE, env=ENV)

    # Start Flask in a thread (optional webhook endpoint)
    def run_api():
        app.run(host='0.0.0.0', port=8080)

    Thread(target=run_api, daemon=True).start()

    # Polling loop
    while True:
        try:
            err = prom_query(q_err_rate(WINDOW))
            p90 = prom_query(q_p90(WINDOW))
            jlog('ctrl_tick', err=err, p90=p90, rate=rate)
            if err is None or p90 is None:
                time.sleep(INTERVAL)
                continue

            now = time.time()
            if (err > ERR_HIGH or p90 > LAT_HIGH) and (now - last_change_ts >= COOLDOWN):
                nr = adjust(rate, up=True)
                if nr != rate:
                    jlog('ctrl_decision', action='bump', src='poll', from_rate=rate, to_rate=nr,
                         reason={'err': err, 'p90': p90, 'thr_high': {'err': ERR_HIGH, 'p90': LAT_HIGH}})
                    set_rate(nr)
                    rate = nr
                    last_change_ts = now
            elif (err < ERR_LOW and p90 < LAT_LOW) and (now - last_change_ts >= COOLDOWN):
                nr = adjust(rate, up=False)
                if nr != rate:
                    jlog('ctrl_decision', action='decay', src='poll', from_rate=rate, to_rate=nr,
                         reason={'err': err, 'p90': p90, 'thr_low': {'err': ERR_LOW, 'p90': LAT_LOW}})
                    set_rate(nr)
                    rate = nr
                    last_change_ts = now
        except Exception as e:
            jlog('loop_err', error=str(e))
        time.sleep(INTERVAL)

