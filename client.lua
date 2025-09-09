local url = "ws://156.155.82.9:8765/ws"

local ws
local function connect_ws()
    while true do
        local ok, ws_f = pcall(
            http.websocket,
            url
        )
    
        if ok then
            print("connected")
            ws = ws_f
            break
        else
            print("connection failed, retrying in 5 seconds.")
            sleep(5)
        end
    end
end
connect_ws()

-- helper: send a raw message with pcall
local function send_message(msg)
    local ok_send, err = pcall(
        ws.send,
        msg
    )
    if not ok_send then
        print("Failed to send message:", err)
    end
end

-- main loop
while true do
    local ok, err = pcall(function()
        while true do
            local ok, msg = pcall(ws.receive)
            if not ok then
                print("receive err:", textutils.unserialiseJSON(msg))
                return
            end
            msg = textutils.unserialiseJSON(msg)
    
            if not msg then
                print("conn closed, reconnecting")
                ws = connect_ws()
                return
            end
    
            print("received:", msg)
        end
    end)

    if not ok then
        print("error in main loop:", err)
    end
    sleep(0)
end
