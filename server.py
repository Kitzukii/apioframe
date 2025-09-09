from quart import Quart, Blueprint, websocket, jsonify, request
import asyncio
import time
import json
import secrets

# App + Blueprints
app = Quart(__name__)
app.config['SECRET_KEY'] = 'CatsAreCute'

def newBP(name, prefix):
    return Blueprint(name, __name__, url_prefix=prefix)

TURTLE_API = newBP("turtle", "/turtle")
WEB = newBP("web", "/web")

# Keepalive & clients
TIMEOUT = 5  # seconds
clients = {}  # {label: {"ws": websocket, "secret": str, "last_keepalive": float}}

# Error helper
def err(msg):
    return jsonify({"error": msg})

# Example turtle API endpoint
@TURTLE_API.route("/request", methods=["POST"])
async def turtle_request():
    if not request.is_json:
        return err("rq_not_json")
    data = await request.get_json()
    return jsonify({"status": "ok", "received": data})

# Register blueprints
app.register_blueprint(TURTLE_API)
app.register_blueprint(WEB)

# Keepalive monitor
async def keepalive_monitor():
    while True:
        await asyncio.sleep(1)
        now = time.time()
        for label, info in list(clients.items()):
            if now - info["last_keepalive"] > TIMEOUT:
                print(f"Disconnecting turtle '{label}' due to timeout")
                try:
                    await info["ws"].close()
                except:
                    pass
                clients.pop(label, None)

# WebSocket route
@app.websocket("/ws")
async def ws_route():
    ws = websocket._get_current_object()

    # First message must be registration with a label
    try:
        message = await ws.receive()
        data = json.loads(message)
        label = data.get("label")
        if not label:
            await ws.send(json.dumps({"error": "No label provided"}))
            await ws.close()
            return
        if label in clients:
            await ws.send(json.dumps({"error": "Label already in use"}))
            await ws.close()
            return
    except Exception:
        await ws.send(json.dumps({"error": "Invalid registration"}))
        await ws.close()
        return

    # Assign secret token
    client_secret = secrets.token_hex(16)
    clients[label] = {
        "ws": ws,
        "secret": client_secret,
        "last_keepalive": time.time()
    }

    print(f"Turtle connected: '{label}' (secret: {client_secret})")

    # Send label and secret to client
    await ws.send(json.dumps({
        "type": "init",
        "label": label,
        "secret": client_secret
    }))

    # Initial keepalive ping
    await ws.send(json.dumps({"type": "keepalive", "msg": "ping"}))

    try:
        while True:
            message = await ws.receive()
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = message  # raw string

            # Keepalive
            if isinstance(data, dict) and data.get("type") == "keepalive":
                clients[label]["last_keepalive"] = time.time()
                print(f"Keepalive from '{label}': {data}")
            else:
                # Echo message
                print(f"Message from '{label}': {data}")
                await ws.send(json.dumps({"echo": data, "from": label}))
    except Exception as e:
        print(f"Turtle '{label}' disconnected ({e})")
    finally:
        clients.pop(label, None)

# Send a message to a specific turtle by label
async def send_to_turtle(label, message):
    info = clients.get(label)
    if not info:
        print(f"No turtle with label '{label}' connected")
        return False
    ws = info["ws"]
    await ws.send(json.dumps(message))
    return True

@app.before_serving
async def startup():
    asyncio.create_task(keepalive_monitor())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
