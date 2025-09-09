-- CC WebSocket client for your server
local url = "ws://156.155.82.9:8765/ws"

-- Read label from file safely
local function getLabel()
    if fs.exists("label.txt") then
        local f = fs.open("label.txt", "r")
        local label = f.readAll()
        f.close()
        return label
    end
    return "default_turtle"
end

local label = getLabel()
local ws = nil

-- Attempt to connect and register the label
local function connect_ws()
    while true do
        local ok, ws_f = pcall(http.websocket, url)
        if ok and ws_f then
            ws = ws_f
            print("connected")

            -- register label safely
            local ok_reg, err = pcall(function()
                ws:send(textutils.serialiseJSON({label = label}))
            end)

            if ok_reg then
                print("registered label:", label)
                return ws
            else
                print("Failed to register:", err)
                ws:close()
                ws = nil
            end
        else
            print("connection failed, retrying in 5s")
        end
        sleep(5)
    end
end

-- Helper to safely send a message
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

-- Main loop: receive messages and respond to keepalive
while true do
    if not ws then
        ws = connect_ws()
    end

    local ok, err = pcall(function()
        while true do
            if not ws then return end

            -- receive safely
            local ok_recv, msg = pcall(function() return ws:receive() end)
            if not ok_recv then
                print("receive error:", msg)
                ws:close()
                ws = nil
                return
            end

            if not msg then
                print("connection closed, reconnecting")
                ws:close()
                ws = nil
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
        if ws then
            ws:close()
            ws = nil
        end
    end

    sleep(0)
end
