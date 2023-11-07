local cpath = "/www/server/total/"
if not package.cpath:find(cpath) then
    package.cpath = cpath .. "?.so;" .. package.cpath
end
if not package.path:find(cpath) then
	package.path = cpath .. "?.lua;" .. package.path
end

local memcached = nil
local domains = nil
local presult, err = pcall(
    function()
		memcached = require "memcached"
        domains = require "domains"
    end
)

if not presult then return end
cache = memcached.Connect("127.0.0.1", 11211)
if not cache then
	cache = memcached.Connect("localhost", 11211)
end
if not cache then return true end

-- clear cache
local time_key = os.date("%Y%m%d%H", os.time())
for _i, v in pairs(domains) do
    name = v["name"]
    -- print("cleaning "..name.."'s cache...")
    cache:delete(name.."client_stat"..time_key)
    cache:delete(name.."_STORING")
    cache:delete(name.."_STORE_START")
    cache:delete(name.."spider_stat"..time_key)
    local cache_key = name.."request_stat"..time_key
    cache:delete(cache_key)
    -- print(cache_key)
end

