local url = "ws://156.155.82.9:8765/ws"

local ws

local function getLabel()
    return fs.open("label.txt", "r").readAll()
end
local label = "wawa"

local function connect_ws()
    while true do
        local ok, ws_f = pcall(http.websocket, url)
        if ok and ws_f then
            ws = ws_f
            print("connected")

            -- send registration message
            local ok_send, err = pcall(function()
                ws:send(textutils.serialiseJSON({label=label}))
            end)
            if not ok_send then
                print("Failed to register:", err)
                sleep(5)
            else
                break
            end
        else
            print("connection failed, retrying in 5 seconds.")
            sleep(5)
        end
    end
end

connect_ws()

-- helper: send a raw message safely
local function send_message(msg)
    local ok_send, err = pcall(ws.send, ws, textutils.serialiseJSON(msg))
    if not ok_send then
        print("Failed to send message:", err)
    end
end

-- main loop
while true do
    local ok, err = pcall(function()
        while true do
            local ok_recv, msg = pcall(ws.receive, ws)
            if not ok_recv then
                print("receive error:", msg)
                ws = connect_ws()
                return
            end

            if not msg then
                print("conn closed, reconnecting")
                ws = connect_ws()
                return
            end

            local data = textutils.unserialiseJSON(msg)
            if data then
                if data.type == "keepalive" then
                    -- respond to keepalive pings
                    send_message({type="keepalive", msg="pong"})
                else
                    print("received:", data)
                end
            end
        end
    end)

    if not ok then
        print("error in main loop:", err)
    end
    sleep(0)
end
