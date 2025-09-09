local ws, err = http.websocket("ws://156.155.82.9:8765")
if not ws then error(err) end

local function send(id, result)
    ws.send(textutils.serialiseJSON({id=id,result=result}))
end

local function run_code(code)
    local f, err = loadstring(code)
    if not f then return err end
    local ok, res = pcall(f)
    return ok and res or res
end

local function run_scan()
    local scan = {}
    for i=1,6 do
        local s, d = turtle.inspect()
        if s then
            table.insert(scan,{name=d.name,x=0,y=0,z=0})
        end
        turtle.turnRight()
    end
    return scan
end

local function get_location()
    local x,y,z = gps.locate()
    return {x=x,y=y,z=z}
end

local function get_full_state()
    return {
        fuel=turtle.getFuelLevel(),
        slot=turtle.getSelectedSlot(),
        location=get_location(),
    }
end

local function move(direction)
    if direction=="up" then return turtle.up()
    elseif direction=="down" then return turtle.down()
    elseif direction=="forward" then return turtle.forward()
    elseif direction=="back" then return turtle.back()
    elseif direction=="left" then turtle.turnLeft() return true
    elseif direction=="right" then turtle.turnRight() return true
    end
    return false
end

while true do
    local msg = ws.receive()
    if not msg then break end
    local data = textutils.unserializeJSON(msg)
    if data.action == "run_code" then
        send(data.id, run_code(data.code))
    elseif data.action == "run_scan" then
        send(data.id, run_scan())
    elseif data.action == "get_location" then
        send(data.id, get_location())
    elseif data.action == "get_full_state" then
        send(data.id, get_full_state())
    elseif data.action == "move" then
        send(data.id, move(data.direction))
    end
end
