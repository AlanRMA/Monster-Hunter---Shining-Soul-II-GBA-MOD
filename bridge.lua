-- Load this file in mGBA: Tools -> Scripting -> Load script.
-- Protocol: one JSON request and response per line, TCP 127.0.0.1:8765.
-- Example: {"id":1,"command":"read_range","params":{"address":"0x0600E800","length":2048}}
local dir = (script and script.dir) or debug.getinfo(1, 'S').source:sub(2):match('^(.*)[/\\]') or '.'
local json = dofile(dir .. '/json.lua')
if SS2_BRIDGE and SS2_BRIDGE.stop then SS2_BRIDGE.stop() end
local bridge = { clients = {}, server = nil }
SS2_BRIDGE = bridge

local function number(v, name)
    local n = type(v) == 'number' and v or tonumber(v)
    assert(n and n >= 0 and n % 1 == 0 and n <= 0xffffffff, 'invalid ' .. name)
    return n
end
local function need_emu() assert(emu, 'load a ROM first') end
local function read_width(width, address)
    -- readRange uses bus reads consistently in mGBA 0.10.x.
    local bytes = emu:readRange(address, width)
    local value = 0
    for i = 1, width do value = value | (bytes:byte(i) << ((i - 1) * 8)) end
    return value
end
local function hex(bytes) return (bytes:gsub('.', function(c) return string.format('%02x', c:byte()) end)) end
local handlers = {}
handlers.ping = function() return 'pong' end
handlers.get_info = function()
    need_emu()
    return { title = emu:getGameTitle(), code = emu:getGameCode(), rom_size = emu:romSize(), version = system and system.version or 'unknown' }
end
for _, width in ipairs({ 1, 2, 4 }) do
    handlers['read' .. width * 8] = function(p)
        need_emu()
        local address = number(p.address, 'address')
        return { address = address, value = read_width(width, address) }
    end
    handlers['write' .. width * 8] = function(p)
        need_emu()
        local address = number(p.address, 'address')
        local value = number(p.value, 'value')
        assert(value < 2 ^ (width * 8), 'value exceeds write width')
        emu['write' .. width * 8](emu, address, value)
        return { address = address, value = read_width(width, address) }
    end
end
handlers.read_range = function(p)
    need_emu()
    local address = number(p.address, 'address')
    local length = number(p.length or p.size, 'length')
    assert(length <= 0x40000, 'range too large')
    return { address = address, length = length, encoding = 'hex', data = hex(emu:readRange(address, length)) }
end
handlers.read_register = function(p) need_emu(); return emu:readRegister(assert(p.name or p.register, 'register required')) end
handlers.set_keys = function(p) need_emu(); emu:setKeys(number(p.keys or p.mask, 'keys')); return true end
handlers.reset = function() need_emu(); emu:reset(); return true end
handlers.load_rom = function(p) need_emu(); return emu:loadFile(assert(p.path, 'path required')) end
handlers.screenshot = function(p) need_emu(); emu:screenshot(assert(p.path, 'path required')); return { path = p.path } end
handlers.save_state = function(p) need_emu(); return emu:saveStateFile(assert(p.path, 'path required')) end
handlers.load_state = function(p) need_emu(); return emu:loadStateFile(assert(p.path, 'path required')) end

local function dispatch(line)
    local request
    local ok, result = pcall(function()
        request = json.decode(line)
        assert(type(request) == 'table', 'request must be an object')
        local command = request.command or request.method
        assert(type(command) == 'string', 'command required')
        command = command:gsub('^mgba_', '')
        local fn = assert(handlers[command], 'unknown command: ' .. command)
        return fn(request.params or request.args or request)
    end)
    local reply = { success = ok, id = type(request) == 'table' and request.id or json.null }
    if ok then reply.result = result else reply.error = tostring(result) end
    return json.encode(reply) .. '\n'
end

local function close(client)
    bridge.clients[client] = nil
    pcall(function() client:close() end)
end
function bridge.stop()
    for client in pairs(bridge.clients) do close(client) end
    if bridge.server then bridge.server:close(); bridge.server = nil end
end
local function received(client)
    local state = bridge.clients[client]
    if not state then return end
    while true do
        local chunk, err = client:receive(8192)
        if not chunk or chunk == '' then
            if err ~= socket.ERRORS.AGAIN then close(client) end
            return
        end
        state.buffer = state.buffer .. chunk
        if #state.buffer > 1048576 then close(client); return end
        while true do
            local pos = state.buffer:find('\n', 1, true)
            if not pos then break end
            local line = state.buffer:sub(1, pos - 1)
            state.buffer = state.buffer:sub(pos + 1)
            if line:match('%S') then
                local reply = dispatch(line)
                local sent, senderr = client:send(reply)
                if senderr or not sent or sent < #reply then close(client); return end
            end
        end
    end
end
local server, err = socket.bind('127.0.0.1', 8765)
assert(server, 'SS2 bridge bind failed: ' .. tostring(err))
bridge.server = server
local ok, listenerr = server:listen()
assert(ok, 'SS2 bridge listen failed: ' .. tostring(listenerr))
server:add('received', function()
    local client, accept_error = server:accept()
    if not client then return end
    bridge.clients[client] = { buffer = '' }
    client:add('received', function() received(client) end)
    client:add('error', function() close(client) end)
end)
console:log('SS2 bridge pronta em 127.0.0.1:8765')
