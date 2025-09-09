local url = "ws://156.155.82.9:8765/ws"
local label = "wawa"
local ws

local function connect_ws()
    while true do
        local ok, ws_f = pcall(http.websocket, url)
        if ok and ws_f then
            ws = ws_f
            print("connected")

            -- register label
            local ok_send, err = pcall(function()
                ws:send(textutils.serialiseJSON({label=label}))
            end)

            if ok_send then
                return ws
            else
                print("Failed to register:", err)
                sleep(5)
            end
        else
            print("connection failed, retrying in 5 seconds.")
            sleep(5)
        end
    end
end

ws = connect_ws()

local function send_message(msg)
    if not ws then
        print("Cannot send message: ws is nil")
        return
    end
    local ok, err = pcall(function()
        ws:send(textutils.serialiseJSON(msg))
    end)
    if not ok then
        print("Failed to send message:", err)
    end
end

while true do
    if not ws then
        ws = connect_ws()
    end

    local ok, err = pcall(function()
        while true do
            if not ws then return end
            local ok_recv, msg = pcall(function() return ws:receive() end)
            if not ok_recv then
                print("receive error:", msg)
                ws = connect_ws()
                return
            end

            if not msg then
                print("connection closed, reconnecting")
                ws = connect_ws()
                return
            end

            local data = textutils.unserialiseJSON(msg)
            if data then
                if data.type == "keepalive" then
                    send_message({type="keepalive", msg="pong"})
                else
                    print("received:", data)
                end
            end
        end
    end)

    if not ok then
        print("error in main loop:", err)
        ws = connect_ws()
    end

    sleep(0)
end
