local GITHUB_REPO = 
"https://raw.githubusercontent.com/Ktzukii/<repo>/main/"

local FILES = {
    "agent.lua"
}

local ID_FILE = "agent_id.json"

local function downloadFile(path)
    local url = GITHUB_REPO .. path
    print("Downloading " .. path .. " ...")
    local ok, err = http.get(url)
    if not ok then
        error("Failed to download " .. path .. ": " .. tostring(err))
    end
    local f = fs.open(path, "w")
    f.write(ok.readAll())
    f.close()
    ok.close()
end

for _, f in ipairs(FILES) do
    downloadFile(f)
end

if fs.exists(ID_FILE) then
    print("Identity already exists, skipping registration setup.")
    print("Run `agent.lua` to reconnect.")
    return
end

term.write("Enter label for this turtle/computer: ")
local label = read()

local id = {
    label = label,
}
local f = fs.open(ID_FILE, "w")
f.write(textutils.serializeJSON(id))
f.close()

print("Setup complete! Run `agent.lua` to connect.")
