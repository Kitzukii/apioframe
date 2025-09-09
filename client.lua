-- CC WebSocket client for your server
local url = "ws://156.155.82.9:8765/ws"

-- Read label from file safely
local function getLabel()
    if fs.exists("label.txt") then
        local f = fs.open("label.txt", "r")
        local label = f.readAll():gsub("%s+$", "") -- remove trailing whitespace/newlines
        f.close()
        return label
    end
    return "default_turtle"
end

local label = getLabel()
local ws = nil

-- Helper: safe send
local function send_message(msg)
    if not ws then
        print("Cannot send message: ws is nil")
        return
    end

    local ok_json, json = pcall(textutils.serialiseJSON, msg)
    if not ok_json then
        print("Failed to serialize message:", json)
        return
    end

    local ok_send, err = pcall(function() ws:send(json) end)
    if not ok_send then
        print("Failed to send message:", err)
        if ws then ws:close() end
        ws = nil
    end
end

-- Connect and register label
local function connect_ws()
    while true do
        local ok, ws_f = pcall(http.websocket, url)
        if ok and ws_f then
            ws = ws_f
            print("Connected to server")

            -- Register label safely
            local ok_json, json = pcall(textutils.serialiseJSON, {label = label})
            if not ok_json then
                print("Failed to serialize label:", json)
                ws:close()
                ws = nil
            else
                local ok_send, err = pcall(function() ws:send(json) end)
                if ok_send then
                    print("Registered label:", label)
                    return ws
                else
                    print("Failed to send label:", err)
                    ws:close()
                    ws = nil
                end
            end
        else
            print("Connection failed, retrying in 5s")
        end
        sleep(5)
    end
end

-- Main loop
while true do
    if not ws then
        ws = connect_ws()
    end

    local ok_loop, err = pcall(function()
        while true do
            if not ws then return end

            local ok_recv, msg = pcall(function() return ws:receive() end)
            if not ok_recv then
                print("Receive error:", msg)
                if ws then ws:close() end
                ws = nil
                return
            end

            if not msg then
                print("Connection closed by server, reconnecting")
                if ws then ws:close() end
                ws = nil
                return
            end

            -- Safe JSON parsing
            local ok_data, data = pcall(textutils.unserialiseJSON, msg)
            if ok_data and data then
                if data.type == "keepalive" then
                    send_message({type="keepalive", msg="pong"})
                else
                    print("Received:", data)
                end
            else
                print("Failed to parse JSON:", msg)
            end
        end
    end)

    if not ok_loop then
        print("Error in main loop:", err)
        if ws then ws:close() end
        ws = nil
    end

    sleep(0.05) -- yield slightly to reduce CPU usage
end
