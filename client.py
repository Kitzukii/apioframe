import websockets, json, asyncio

# ws = websocket.create_connection("ws://localhost:8765/ws")

async def hello():
    async with websockets.connect("ws://localhost:8765/ws") as websocket:
        await websocket.send("{'label':'john'}")
        response = await websocket.recv()
        print(f"Received from server: {response}")
        websocket.close()

if __name__ == "__main__":
    asyncio.run(hello())

# try:
#     print("trying to recieve")
#     msg = ws.recv_data()
# except:
#     print("excepted")
# finally:
#     ws.close()

# print(msg)