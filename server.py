from flask import Flask, Blueprint, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
import threading, time

# Error helper
def err(msg):
    return jsonify({"error": msg})

# App + SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'CatsAreCute'
socketio = SocketIO(app, cors_allowed_origins="*")

# Blueprints
TURTLE_API = Blueprint("turtle", __name__, url_prefix="/turtle")
WEB = Blueprint("web", __name__, url_prefix="/web")

# Keepalive tracking
last_keepalive = {}
TIMEOUT = 5  # seconds

def keepalive_monitor():
    while True:
        time.sleep(1)
        now = time.time()
        for sid, last in list(last_keepalive.items()):
            if now - last > TIMEOUT:
                print(f"Disconnecting {sid} due to timeout")
                disconnect(sid)
                last_keepalive.pop(sid, None)

threading.Thread(target=keepalive_monitor, daemon=True).start()

# Example turtle API endpoint
@TURTLE_API.route("/request", methods=["POST"])
def turtle_request():
    if not request.is_json:
        return err("rq_not_json")
    data = request.get_json()
    return jsonify({"status": "ok", "received": data})

# Register blueprints
app.register_blueprint(TURTLE_API)
app.register_blueprint(WEB)

# WebSocket events
@socketio.on("connect")
def t_conn():
    sid = request.sid
    print(f"Client {sid} connected")
    last_keepalive[sid] = time.time()
    emit("keepalive", {"msg": "ping"})  # tell client to reply with anything

@socketio.on("keepalive")
def handle_keepalive(msg=None):
    sid = request.sid
    print(f"Keepalive response from {sid}: {msg}")
    last_keepalive[sid] = time.time()

@socketio.on("message")
def t_msg(msg):
    sid = request.sid
    print(f"Message from {sid}: {msg}")
    emit("message", {"echo": msg})

@socketio.on("disconnect")
def t_deconn():
    sid = request.sid
    print(f"Client {sid} disconnected")
    last_keepalive.pop(sid, None)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8765)
