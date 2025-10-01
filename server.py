import asyncio, time, json, secrets, random
from apioframe_utils import get_rand_name
from quart import Quart, websocket

app = Quart(__name__)

TIMEOUT = 5  # seconds
clients = {}  # {label: {"ws": websocket, "secret": str, "last_keepalive": float}}

# -------- Utility --------
async def safe_send(ws, message: dict):
    try:
        if ws.closed:
            return
        await ws.send(json.dumps(message))
    except Exception:
        pass

async def keepalive_monitor():
    while True:
        await asyncio.sleep(1)
        now = time.time()
        for label, info in list(clients.items()):
            if now - info["last_keepalive"] > TIMEOUT:
                print(f"[TIMEOUT] Disconnecting '{label}'")
                try:
                    await info["ws"].close()
                except:
                    pass
                clients.pop(label, None)

# -------- Websocket handler --------
@app.websocket("/agent")
async def agent():
    ws = websocket._get_current_object()

    label = None
    try:
        # First message must be registration/reconnect
        raw = await ws.receive()
        data = json.loads(raw)

        req_label = data.get("label")
        req_secret = data.get("secret")

        # Handle reconnection
        if req_label and req_secret:
            existing = clients.get(req_label)
            if existing and existing["secret"] == req_secret:
                # replace old ws with new
                existing["ws"] = ws
                existing["last_keepalive"] = time.time()
                await safe_send(ws, {"status": "reconnected", "label": req_label})
                print(f"[RECONNECT] {req_label}")
                label = req_label
            else:
                await safe_send(ws, {"error": "Invalid label or secret"})
                await ws.close()
                return

        else:
            # New registration
            if req_label:
                label = req_label
            else:
                # auto-generate label if missing
                label = f"{get_rand_name}-{random.randrange(0,999)}"

            if label in clients:
                await safe_send(ws, {"error": "Label already in use"})
                await ws.close()
                return

            secret = secrets.token_hex(16)
            clients[label] = {
                "ws": ws,
                "secret": secret,
                "last_keepalive": time.time(),
            }

            await safe_send(ws, {"status": "registered", "label": label, "secret": secret})
            print(f"[REGISTER] {label}")

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

            if data.get("type") == "reboot":
                clients[label]["last_keepalive"] = time.time()
                sendToClient(
                    data.get("label"),
                    "reboot"
                )

            if data.get("type") == "":
                pass

            # print(f"[MSG] from {label}: {data}")

    finally:
        if label and label in clients and clients[label]["ws"] is ws:
            clients.pop(label, None)
            print(f"[DISCONNECT] {label}")

async def sendToClient(label, message):
    info = clients.get(label)
    if not info:
        print(f"No client with label '{label}' connected")
        return False
    await safe_send(info["ws"], message)
    return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keepalive_monitor())
    loop.run_until_complete(app.run_task(host="0.0.0.0", port=5000))
