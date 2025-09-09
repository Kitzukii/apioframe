import asyncio
import json
import threading
from flask import Flask, request, jsonify
import websockets

app = Flask(__name__)
turtle_ws = None
pending_responses = {}

@app.route("/frontend", methods=["POST"])
def frontend():
    global turtle_ws
    if not turtle_ws:
        return jsonify({"error": "Turtle not connected"}), 400
    data = request.json
    action = data.get("action")
    action_id = str(id(data))
    fut = asyncio.get_event_loop().create_future()
    pending_responses[action_id] = fut
    payload = {"id": action_id, "action": action}
    if action == "run_code":
        payload["code"] = data.get("code")
    elif action == "move":
        payload["direction"] = data.get("direction")
    elif action not in ["run_scan", "get_location", "get_full_state"]:
        return jsonify({"error": "Unknown action"}), 400
    asyncio.run_coroutine_threadsafe(
        turtle_ws.send(json.dumps(payload)),
        asyncio.get_event_loop()
    )
    try: # there should be one on it now?
        result = asyncio.run_coroutine_threadsafe(
            wait_for_response(action_id), asyncio.get_event_loop()
        ).result(timeout=10)
        return jsonify(result)
    except asyncio.TimeoutError:
        return jsonify({"error": "Turtle did not respond"}), 504
    finally:
        pending_responses.pop(action_id, None)

async def wait_for_response(action_id):
    fut = pending_responses.get(action_id)
    if fut:
        return await fut
    return None

async def turtle_handler(ws):
    global turtle_ws
    turtle_ws = ws
    try:
        async for msg in ws: # i swear if it crashes the server tho lol
            data = json.loads(msg) # put
            action_id = data.get("id")
            if action_id and action_id in pending_responses:
                fut = pending_responses[action_id]
                if not fut.done():
                    fut.set_result(data.get("result"))
    finally:
        turtle_ws = None

async def ws_server():
    async with websockets.serve(turtle_handler, "", 8765):
        await asyncio.Future()

def start_ws_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_server())

if __name__ == "__main__":
    threading.Thread(target=start_ws_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)