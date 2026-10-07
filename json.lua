-- Small standalone JSON codec for the mGBA bridge (Lua 5.3+).
local json = {}
json.null = setmetatable({}, { __tostring = function() return 'null' end })
local array_mt = {}
function json.array(t) return setmetatable(t or {}, array_mt) end

local escapes = { ['"'] = '\\"', ['\\'] = '\\\\', ['\b'] = '\\b', ['\f'] = '\\f', ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t' }
local function quote(s)
    return '"' .. s:gsub('[%z\1-\31\\"]', function(c)
        return escapes[c] or string.format('\\u%04x', c:byte())
    end) .. '"'
end

function json.encode(value)
    local seen = {}
    local function encode(v)
        if v == json.null or v == nil then return 'null' end
        local kind = type(v)
        if kind == 'string' then return quote(v) end
        if kind == 'boolean' then return tostring(v) end
        if kind == 'number' then
            assert(v == v and v ~= math.huge and v ~= -math.huge, 'non-finite number')
            return tostring(v)
        end
        assert(kind == 'table', 'unsupported JSON type: ' .. kind)
        assert(not seen[v], 'cyclic JSON table')
        seen[v] = true
        local is_array = getmetatable(v) == array_mt or #v > 0
        local parts = {}
        if is_array then
            for k in pairs(v) do assert(type(k) == 'number' and k % 1 == 0 and k >= 1 and k <= #v, 'sparse array') end
            for i = 1, #v do parts[i] = encode(v[i]) end
        else
            for k, item in pairs(v) do
                assert(type(k) == 'string', 'JSON object keys must be strings')
                parts[#parts + 1] = quote(k) .. ':' .. encode(item)
            end
            table.sort(parts)
        end
        seen[v] = nil
        return (is_array and '[' or '{') .. table.concat(parts, ',') .. (is_array and ']' or '}')
    end
    return encode(value)
end

function json.decode(text)
    assert(type(text) == 'string', 'JSON input must be a string')
    local p = 1
    local parse
    local function fail(msg) error(msg .. ' at byte ' .. p, 0) end
    local function skip()
        while text:sub(p, p):match('[ \t\r\n]') do p = p + 1 end
    end
    local function hex4()
        local s = text:sub(p, p + 3)
        if #s ~= 4 or not s:match('^%x%x%x%x$') then fail('invalid Unicode escape') end
        p = p + 4
        return tonumber(s, 16)
    end
    local function parse_string()
        p = p + 1
        local parts = {}
        while p <= #text do
            local c = text:sub(p, p)
            p = p + 1
            if c == '"' then return table.concat(parts) end
            if c == '\\' then
                local e = text:sub(p, p)
                p = p + 1
                local plain = { ['"'] = '"', ['\\'] = '\\', ['/'] = '/', b = '\b', f = '\f', n = '\n', r = '\r', t = '\t' }
                if e == 'u' then
                    local n = hex4()
                    if n >= 0xd800 and n <= 0xdbff then
                        if text:sub(p, p + 1) ~= '\\u' then fail('missing low surrogate') end
                        p = p + 2
                        local low = hex4()
                        if low < 0xdc00 or low > 0xdfff then fail('invalid low surrogate') end
                        n = 0x10000 + (n - 0xd800) * 0x400 + low - 0xdc00
                    elseif n >= 0xdc00 and n <= 0xdfff then fail('unexpected low surrogate') end
                    parts[#parts + 1] = utf8.char(n)
                elseif plain[e] then parts[#parts + 1] = plain[e]
                else fail('invalid escape') end
            else
                if c:byte() < 32 then fail('control character in string') end
                parts[#parts + 1] = c
            end
        end
        fail('unterminated string')
    end
    parse = function(depth)
        if depth > 64 then fail('JSON nesting too deep') end
        skip()
        local c = text:sub(p, p)
        if c == '"' then return parse_string() end
        if c == '{' or c == '[' then
            local array = c == '['
            local closing = array and ']' or '}'
            local t = array and json.array() or {}
            p = p + 1
            skip()
            if text:sub(p, p) == closing then p = p + 1; return t end
            while true do
                local key
                if not array then
                    if text:sub(p, p) ~= '"' then fail('expected object key') end
                    key = parse_string()
                    skip()
                    if text:sub(p, p) ~= ':' then fail('expected colon') end
                    p = p + 1
                end
                local value = parse(depth + 1)
                if array then t[#t + 1] = value else t[key] = value end
                skip()
                c = text:sub(p, p)
                p = p + 1
                if c == closing then return t end
                if c ~= ',' then fail('expected comma or closing delimiter') end
                skip()
            end
        end
        for token, value in pairs({ ['true'] = true, ['false'] = false, ['null'] = json.null }) do
            if text:sub(p, p + #token - 1) == token then p = p + #token; return value end
        end
        local token = text:sub(p):match('^-?%d+%.?%d*[eE]?[+-]?%d*')
        if token and token ~= '' then
            if token:match('^-?0%d') or token:match('%.$') or token:match('[eE][+-]?$') then fail('invalid number') end
            local value = tonumber(token)
            if not value or value == math.huge or value == -math.huge then fail('invalid number') end
            p = p + #token
            return value
        end
        fail('invalid JSON value')
    end
    local value = parse(0)
    skip()
    if p <= #text then fail('trailing JSON data') end
    return value
end

return json
