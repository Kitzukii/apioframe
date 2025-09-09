local url = "ws://localhost:5000/socket"
sleep = function(t) sleep(t) end

local function connect_ws()
    while true do
        local ok, ws = pcall(function()
            return http.websocket(url)
        end)
    
        if ok then
            print("connected")
            return ws, true
        else
            print("connection failed, retrying in 5 seconds.")
            sleep(5)
        end
    end
end

connect_ws()

-- helper: send a raw message with pcall
local function send_message(msg)
    local ok_send, err = pcall(function()
        ws.send(msg)
    end)
    if not ok_send then
        print("Failed to send message:", err)
    end
end

-- main loop
while true do
    local ok, err = pcall(function()
        while true do
            local ok, msg = pcall(function() return ws.receive() end)
            if not ok then
                print("receive err:", msg)
                return
            end
    
            if not msg then
                print("conn closed, reconnecting")
                connect_ws()
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
