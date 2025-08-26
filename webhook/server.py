from flask import Flask, request
import sys, json

app = Flask(__name__)

@app.route('/', methods=['POST'])
def recv():
    payload = request.get_json(silent=True)
    print('ALERT_WEBHOOK:', json.dumps(payload), file=sys.stdout, flush=True)
    return 'ok\n'

@app.route('/', methods=['GET'])
def probe():
    return 'ready\n'

