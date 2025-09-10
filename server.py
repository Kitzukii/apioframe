import asyncio, time, json, secrets
from quart import Quart, Blueprint, jsonify, request, render_template
import websockets

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

async def safe_send(ws, message: dict):
    try:
        if ws.closed:
            return
        await ws.send(json.dumps(message))
    except websockets.exceptions.ConnectionClosed:
        pass
    
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

async def ws_handler(ws, path):
    try:
        message = await ws.recv()
        data = json.loads(message)
        label = data.get("label")
        if not label:
            await safe_send(ws, {"error": "No label provided"})
            await ws.close()
            return
        if label in clients:
            await safe_send(ws, {"error": "Label already in use"})
            await ws.close()
            return
    except Exception:
        await safe_send(ws, {"error": "Invalid registration"})
        try:
            await ws.close()
        except:
            pass
        return

# Function to send data to a client
async def sendToClient(label, message):
    info = clients.get(label)
    if not info:
        print(f"No client with label '{label}' connected")
        return False
    ws = info["ws"]
    await ws.send(json.dumps(message))
    return True

# Run both Quart + websockets server
async def main():
    # Start keepalive
    asyncio.create_task(keepalive_monitor())

    # Start websocket server
    ws_server = await websockets.serve(ws_handler, "0.0.0.0", 8765)

    # Start Quart server
    quart_task = asyncio.create_task(app.run_task(host="0.0.0.0", port=5000))

    await asyncio.gather(ws_server.wait_closed(), quart_task)

if __name__ == "__main__":
    asyncio.run(main())
