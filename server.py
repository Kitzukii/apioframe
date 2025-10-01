import asyncio, time, json, secrets, uuid
from quart import Quart, websocket

app = Quart(__name__)

# Keepalive & clients
TIMEOUT = 5  # seconds
clients = {}  # {label: {"ws": websocket, "secret": str, "last_keepalive": float}}

# Safe send wrapper
async def safe_send(ws, message: dict):
    try:
        if ws.closed:
            return
        await ws.send(json.dumps(message))
    except Exception:
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

@app.websocket("/agent")
async def agent():
    ws = websocket._get_current_object()

    try:
        # initial registration
        message = await ws.receive()
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

        secret = secrets.token_hex(16)
        clients[label] = {
            "last_keepalive": time.time(),
            "uuid": uuid.uuid4(),
            "secret": secret,
            "conn": ws
        }

        await safe_send(ws, {"status": "registered", "secret": secret})
        print(f"Client '{label}' connected")

        while True:
            try:
                raw = await ws.receive()
            except Exception:
                break

            try:
                data = json.loads(raw)
            except:
                continue

            if data.get("type") == "keepalive":
                clients[label]["last_keepalive"] = time.time()
                continue

            print(f"Received from {label}: {data}")
    finally:
        if label in clients:
            clients.pop(label, None)
        print(f"Client '{label}' disconnected")

async def sendTo(label, message):
    info = clients.get(label)
    if not info:
        print(f"No client with label '{label}' connected")
        return False
    ws = info["ws"]
    await safe_send(ws, message)
    return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keepalive_monitor())
    loop.run_until_complete(app.run_task(host="0.0.0.0", port=5000))
