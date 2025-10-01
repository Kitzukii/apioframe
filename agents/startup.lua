local wsUrl = "ws://152.53.163.224:8765/agent"
local KEEPALIVE_INTERVAL = 2
local ID_FILE = "agent.json"
local json = textutils



local identity
if fs.exists(ID_FILE) then
    local f = fs.open(ID_FILE, "r")
    identity = json.unserializeJSON(f.readAll())
    f.close()
end
if not identity or not identity.label then
    print("No identity found, please run setup.lua")
    return
end

print("Connecting to server ⋉"..wsUrl.."⋊")
local ws, err = http.websocket(wsUrl)
if not ws then
    print("Failed to connect:", err)
    return
end

if identity.secret then
    print("Reconnecting.")
    ws.send(json.serialize({ label = identity.label, secret = identity.secret }))
else
    print("Registering.")
    ws.send(json.serialize({ label = identity.label }))
end

-- Wait for server response
local raw = ws.receive(5)
if not raw then
    print("No response from server.")
    ws.close()
    return
end

local data = json.unserialize(raw)
if data.error then
    print("Server error:", data.error)
    ws.close()
    return
end

-- Save secret if provided
if data.secret and not identity.secret then
    identity.secret = data.secret
    local f = fs.open(ID_FILE, "w")
    f.write(json.serializeJSON(identity))
    f.close()
    print("Identity saved with secret.")
end

print("Connected as " .. identity.label)

-- Keepalive loop
local function keepalive()
    while true do
        sleep(KEEPALIVE_INTERVAL)
        if ws then
            ws.send(json.serialize({ type = "keepalive" }))
        end
    end
end

-- Listener loop
local function listen()
    while true do
        local msg = ws.receive()
        if not msg then
            print("Disconnected from server.")
            return
        end

        local ok, packet = pcall(json.unserialize, msg)
        if ok and type(packet) == "table" then
            print("Message from server:", textutils.serialize(packet))
        else
            print("Invalid packet:", msg)
        end
    end
end

parallel.waitForAny(keepalive, listen)
ws.close()
