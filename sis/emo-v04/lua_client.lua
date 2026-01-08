-- LUA Socket Client Example
-- LuaSocket 라이브러리가 필요합니다. (일반적인 Lua 환경)
-- 게임 내 LUA 환경이라면 해당 게임의 소켓 API로 대체해야 합니다.

local socket = require("socket")

local host = "127.0.0.1"
local port = 5000

local tcp = assert(socket.tcp())

print("Connecting to " .. host .. ":" .. port)
-- 연결 시도
local res, err = tcp:connect(host, port)

if not res then
    print("Connection failed: " .. err)
    return
end

print("Connected! Type 'quit' to exit.")

while true do
    io.write("You (LUA): ")
    local input = io.read()
    if not input or input == "quit" then break end

    -- 서버로 전송 (줄바꿈 포함)
    tcp:send(input .. "\n")

    -- 서버 응답 수신
    local s, status, partial = tcp:receive()
    print("Server (Bot): " .. (s or partial or status))
end

tcp:close()