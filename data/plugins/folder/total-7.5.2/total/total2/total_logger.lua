--------------------------------------------------------------------------------
--------------------------宝塔监控报表插件lua端统计代码---------------------------
--------------------------Author: linxiao<940950943@qq.com>---------------------
--------------------------如遇到问题请到QQ群625962236寻求帮助---------------------
--------------------------------------------------------------------------------
local debug_mode                       = false
local version                          = "2.1"
local cpath                            = "/www/server/total/"
local cache                            = ngx.shared.bt_total
local string_find                      = string.find
local string_gsub                      = string.gsub
local string_match                     = string.match
local string_lower                     = string.lower
local string_sub                       = string.sub
local string_len                       = string.len
local timer_at                         = ngx.timer.at
local ngx_re_match                     = ngx.re.match
local ngx_re_gmatch                    = ngx.re.gmatch
local ngx_re_find                      = ngx.re.find
local ngx_re_sub                       = ngx.re.sub
local ngx_var                          = ngx.var
local ngx_req                          = ngx.req
local io_open                          = io.open
local fake_spider                      = 77
local spider_cache_prefix              = "MATCH_SPIDER_"
local spider_cache_timeout             = 86400
local client_cache_prefix              = "MATCH_CLIENT_"
local ip_spider_prefix                 = "IP_SPIDER_"
local latest_reload_ips                = "LATEST_RELOAD_IPS"
local client_cache_timeout             = 86400
local ONE_DAY_TIMEOUT                  = 86400
local SEVEN_DAY_TIMEOUT                = 86400 * 7
local total_db_name                    = "total.db"
local cache_count_threshold            = 300
local cache_interval_threshold         = 10
local no_binding_server_name           = "btunknownbt"
local cache_check_key_prefix           = "CACHE_CHECK_"
local store_interval                   = 30  -- s
local succ, new_tab                    = pcall(require, "table.new")
if not succ then
	new_tab = function() return {} end
end
local server_name,server_port,ip,today,day,body_length,method,config,cache_count,hour_str
local status_code
local json, sqlite3 
local total_config, clients
local update_day
local data_dir
local number_day
local day_column
local flow_column
local spider_column
local day_hour1_column                 = "day_hour1"
local flow_hour1_column                = "flow_hour1"
local spider_hour1_column              = "spider_flow_hour1"
local client_port
local total_db, logs_db
local logger_inited
local run_error
local error_msg
local statistics_machine_access
local global_config
local domains
local sites
local local_site_config
local uri
local spider_version
local spider_table
local spider_names
local error_codes
local http_methods
local site_config

local _M = new_tab(0, 10)

local is_exiting
if not ngx.config or not ngx.config.ngx_lua_version
    or ngx.config.ngx_lua_version < 9003 then
    is_exiting = function() return false end
else
    is_exiting = ngx.worker.exiting
end

local function debug(msg, server_name)
	if not debug_mode then return true end
	local fp = io_open('/www/server/total/debug.log', 'ab') if fp == nil then
    	return nil
	end
	local localtime = os.date("%Y-%m-%d %H:%M:%S")
	if server_name then
		fp:write(server_name.."/"..localtime..":"..tostring(msg) .. "\n")
		-- fp:write(tostring(msg) .. "\n")
	else
		fp:write(localtime..":"..tostring(msg) .. "\n")
	end
	fp:flush()
	fp:close()
	return true
end

function _M.inited()
	return logger_inited
end

function _M.runtime_error()
	return run_error
end

local function get_config(site)
	-- local config_data = json.decode(read_file_body_bylog(cpath..'/config.json'))
	if local_site_config[site] then
		return local_site_config[site]
	end

	local config_data = total_config
	local conf = nil
	if config_data["global"] == nil then return nil end
	local global_config = config_data["global"]
	if config_data[site] == nil then
		conf = global_config
	else
		conf = config_data[site]
		for k, v in pairs(global_config) do
			if conf[k] == nil then
				conf[k] = v
			end
		end
	end
	if site == no_binding_server_name then
		local_site_config[site] = conf
		return conf
	end
	local_site_config[site] = conf
	return conf
end

-- , cache_expired=
local function file_exists(filename)
	if not filename then return false end
	local file = io_open(filename, "rb")
	if file then 
		file:close()
		return true 
	end
	return false
end

local function check_dir(path)
	local file = io_open(path, "rb")
	if file then file:close() end
	return file ~= nil
end

local function is_migrating(store_server_name)
	local file = io_open("/www/server/total/migrating", "rb")
	if file then return true end
	local file = io_open("/www/server/total/logs/"..store_server_name.."/migrating", "rb")
	if file then return true end
	return false
end

local function get_server_name(c_name)
	local cache_key
	if c_name == no_binding_server_name then
		return no_binding_server_name
	end
	if c_name == "127.0.0.1" then
		return c_name
	end

	cache_key = c_name .. server_port
	local my_name = cache:get(cache_key)
	if my_name then
		--debug("get_server_name from cache:"..my_name)
		return my_name
    end
	local cache_timeout = 3600
	if domains[c_name] then
		c_name = string_gsub(c_name,'_','.')
    	--cache:set(c_name, c_name, cache_timeout)
		--debug("get_server_name from domains:"..c_name)
		cache:set(cache_key, c_name, cache_timeout)
		return c_name
	end

	local simple_domain

	local s,e = string_find(c_name, "[.]")
	if s and e then
		simple_domain = string_sub(c_name, s+1)
	end

	local pending_name
	local _normal
	local _port
	for site_name,v in pairs(domains)
	do
		_normal = v["normal"]
		_port = v["port"]

        if type(_port[tostring(server_port)]) then
            if _normal and _port[tostring(server_port)] then
    			if _normal[c_name] then
    				site_name = string_gsub(site_name,'_','.')
    				cache_key = site_name .. server_port
    				--cache:set(c_name, site_name, cache_timeout)
    				cache:set(cache_key, site_name, cache_timeout)
    				-- debug("_port[tostring(server_port)]: " .. tostring(_port[tostring(server_port)]))
    				-- debug("site_name: " .. tostring(site_name))
					--debug("get_server_name from _normal:"..site_name)
    				return site_name
    			end
    			-- 带*泛域名匹配优先级最低, 不直接返回
    			if simple_domain and _normal[simple_domain] then
    				pending_name = site_name
    			end
    		end
        else
            if _normal then
    			if _normal[c_name] then
    				site_name = string_gsub(site_name,'_','.')
    				cache_key = site_name .. server_port
    				--cache:set(c_name, site_name, cache_timeout)
    				cache:set(cache_key, site_name, cache_timeout)
    				return site_name
    			end
    			-- 带*泛域名匹配优先级最低, 不直接返回
    			if simple_domain and _normal[simple_domain] then
    				pending_name = site_name
    			end
    		end
        end
	end
	if pending_name then
		-- ngx.log(ngx.ERR, "Get server name from pending, "..c_name.."/"..pending_name)
		pending_name = string_gsub(pending_name,'_','.')
    	--cache:set(c_name, pending_name, cache_timeout)
		cache:set(cache_key, pending_name, cache_timeout)
		return pending_name
	end
    --cache:set(c_name, no_binding_server_name,cache_timeout)
	cache:set(cache_key, no_binding_server_name, cache_timeout)
	return no_binding_server_name
end

local function create_dir(path, create_server_name)
	if ngx_re_match(path,'/\\.\\./') then return false end
	local legal = true
	if not ngx_re_match(path,'^/www/server/total/') then 
		legal = false
	end
	if data_dir then
		if not ngx_re_match(path,'^'..data_dir) then
			legal = false
		else
			legal = true
		end
	end
	if not legal then
		return false
	end
	local check_name = get_server_name(create_server_name)
	local res = ngx_re_find(path, "(\\&|\\{|\\}|\\%|\\$|\\+|\\=|\\*|\\@|\\'|\\\"|\\[|\\])")
	if res then
		-- debug("非法字符。")
		return false
	end
	os.execute("mkdir -p " .. path)
	return true
end

local function write_file_bylog(filename,body,mode)
	local fp = io_open(filename,mode)
	if fp == nil then
		return nil
	end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end

local function read_file_body_bylog(filename)
	local fp = io_open(filename,'rb')
	if not fp then
		return nil
	end
	fbody = fp:read("*a")
	fp:close()
	if fbody == '' then
		return nil
	end
	return fbody
end

local function split_bylog(str,reps)
	local resultStrList = {}
	string_gsub(str,'[^'..reps..']+',function(w) table.insert(resultStrList,w) end)
	return resultStrList
end

local function arrlen_bylog(arr)
	if not arr then return 0 end
	count = 0
	for _,v in ipairs(arr) do
		count = count + 1
	end
	return count
end

local function is_ipaddr_bylog(client_ip)
	local cipn = split_bylog(client_ip,'.')
	if arrlen_bylog(cipn) < 4 then return false end
	for _,v in ipairs({1,2,3,4})
	do
		local ipv = tonumber(cipn[v])
		if ipv == nil then return false end
		if ipv > 255 or ipv < 0 then return false end
	end
	return true
end

local function get_client_ip_bylog()
	local client_ip = "unknown"
	local cdn = config['cdn']
	if cdn == true then
		for v,_ in pairs(config['cdn_headers']) do
			-- debug("get client ip from header["..v.."].")
			if request_header[v] ~= nil and request_header[v] ~= "" then
				local ip_list = request_header[v]
				if type(ip_list) == 'table' then
					ip_list = ip_list[0]
					if not ip_list then
						break
					end
				end
				client_ip = split_bylog(ip_list,',')[1]
				break;
			end
		end
	end
	if type(client_ip) == 'table' then client_ip = "" end
	if client_ip ~= "unknown" and string_match(client_ip,"^[%w:]+$") then
		return client_ip
	end
	if string_match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil or not is_ipaddr_bylog(client_ip) then
		client_ip = ngx_var.remote_addr
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

local function arrip_bylog(ipstr)
	if ipstr == 'unknown' then return {0,0,0,0} end
	iparr = split_bylog(ipstr,'.')
	iparr[1] = tonumber(iparr[1])
	iparr[2] = tonumber(iparr[2])
	iparr[3] = tonumber(iparr[3])
	iparr[4] = tonumber(iparr[4])
	return iparr
end

local function get_request_time()
	local request_time = math.floor((ngx.now() - ngx_req.start_time()) * 1000)
	if request_time == 0 then  request_time = 1 end
	return request_time
end

local function get_length(k)
	local clen  = ngx_var.body_bytes_sent
	if clen == nil then clen = 0 end
	return tonumber(clen)
end

local function get_boundary()
	local header = request_header["content-type"]
	if not header then return nil end
	if type(header) == "table" then
		return false
	end
	if header then
		if ngx_re_find(header,[[multipart]],'ijo') then
			if not ngx_re_match(header,'^multipart/form-data; boundary=') then 
				return false
			end
		   	local multipart_data=ngx_re_match(header,'^multipart/form-data; boundary=.+')
			local check_file=ngx_re_gmatch(multipart_data[0],[[=]],'ijo')
			ret={}
			while true do
				local m, err = check_file()
				if m then 
					table.insert(ret,m)
				else
					break
				end 
			end
			if type(ret)~='table' then return false end 
			if(arrlen_bylog(ret)>=2) then
				return false
			end
			return header
		else
			return false
		end 
	end 
end

local function get_http_original()
	local data = ""
	local headers = ngx_req.get_headers()
	if not headers then return data end
	if method ~='GET' then 
		data = ngx_req.get_body_data()
		if not data then
			data = ngx_req.get_post_args(1000000)
		end
		if "string" == type(data) then
			headers["payload"] = data
		end

		if "table" == type(data) then
			headers = table.concat(headers, data)
		end
	end
	return json.encode(headers)
end

local function init_total_db(log_dir, server_name, db_name)
	-- 初始化统计数据库
	local path = log_dir .. "/" .. server_name
	if not check_dir(path) then 
		res = create_dir(path, server_name) 
		if not res then
			return false
		end
		-- debug("create dir res:"..tostring(res))
	end
	local db_path = path .. "/" .. db_name
	if cache:get(db_path) then
		return
	end
	local db = sqlite3.open(db_path)
	if not db then
		return false
	end
	local table_name = "request_stat"
	local stmt = db:prepare("SELECT COUNT(*) FROM sqlite_master where type='table' and name=?")
	local rows = 0
	if stmt ~= nil then
		stmt:bind_values(table_name)
		stmt:step()
		rows = stmt:get_uvalues()
		stmt:finalize()
	end
	if stmt ~= nil and rows >0 then
		cache:set(db_path, true)
	else
		status, errorString = db:exec([[PRAGMA synchronous = 0]])
		status, errorString = db:exec([[PRAGMA page_size = 4096]])
		status, errorString = db:exec([[PRAGMA journal_mode = wal]])
		status, errorString = db:exec([[PRAGMA journal_size_limit = 1073741824]])
		status, errorString = db:exec([[
			CREATE TABLE client_stat(
				time INTEGER PRIMARY KEY,
				weixin INTEGER DEFAULT 0,
				android INTEGER DEFAULT 0,
				iphone INTEGER DEFAULT 0,
				mac INTEGER DEFAULT 0,
				windows INTEGER DEFAULT 0,
				linux INTEGER DEFAULT 0,
				edeg INTEGER DEFAULT 0,
				firefox INTEGER DEFAULT 0,
				msie INTEGER DEFAULT 0,
				metasr INTEGER DEFAULT 0,
				qh360 INTEGER DEFAULT 0,
				theworld INTEGER DEFAULT 0,
				tt INTEGER DEFAULT 0,
				maxthon INTEGER DEFAULT 0,
				opera INTEGER DEFAULT 0,
				qq INTEGER DEFAULT 0,
				uc INTEGER DEFAULT 0,
				pc2345 INTEGER DEFAULT 0, 
				safari INTEGER DEFAULT 0,
				chrome INTEGER DEFAULT 0,
				machine INTEGER DEFAULT 0,
				mobile INTEGER DEFAULT 0,
				other INTEGER DEFAULT 0
			)]])

		-- 请求分类统计明细，按小时统计
		-- time: 2021032500 时间刻度, 以小时为单位
		status, errorString = db:exec([[
			CREATE TABLE request_stat(
				time INTEGER PRIMARY KEY,
				req INTEGER DEFAULT 0,
				pv INTEGER DEFAULT 0,
				uv INTEGER DEFAULT 0,
				ip INTEGER DEFAULT 0,
				length INTEGER DEFAULT 0,
				spider INTEGER DEFAULT 0,
				status_500 INTEGER DEFAULT 0,
				status_501 INTEGER DEFAULT 0,
				status_502 INTEGER DEFAULT 0,
				status_503 INTEGER DEFAULT 0,
				status_504 INTEGER DEFAULT 0,
				status_505 INTEGER DEFAULT 0,
				status_506 INTEGER DEFAULT 0,
				status_507 INTEGER DEFAULT 0,
				status_509 INTEGER DEFAULT 0,
				status_510 INTEGER DEFAULT 0,
				status_400 INTEGER DEFAULT 0,
				status_401 INTEGER DEFAULT 0,
				status_402 INTEGER DEFAULT 0,
				status_403 INTEGER DEFAULT 0,
				status_404 INTEGER DEFAULT 0,
				http_get INTEGER DEFAULT 0,
				http_post INTEGER DEFAULT 0,
				http_put INTEGER DEFAULT 0,
				http_patch INTEGER DEFAULT 0,
				http_delete INTEGER DEFAULT 0
			)]])
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_405 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_406 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_407 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_408 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_409 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_410 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_411 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_412 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_413 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_414 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_415 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_416 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_417 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_418 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_421 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_422 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_423 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_424 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_425 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_426 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_449 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_451 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN status_499 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE request_stat ADD COLUMN fake_spider INTEGER DEFAULT 0;")	

		-- 蜘蛛统计明细，按小时统计
		-- 按照已有蜘蛛分类，分别建立对应的统计列。
		status, errorString = db:exec[[
			CREATE TABLE spider_stat(
				time INTEGER PRIMARY KEY,
				bytes INTEGER DEFAULT 0,
				bing INTEGER DEFAULT 0,
				soso INTEGER DEFAULT 0,
				yahoo INTEGER DEFAULT 0,
				sogou INTEGER DEFAULT 0,
				google INTEGER DEFAULT 0,
				baidu INTEGER DEFAULT 0,
				qh360 INTEGER DEFAULT 0,
				youdao INTEGER DEFAULT 0,
				yandex INTEGER DEFAULT 0,
				dnspod INTEGER DEFAULT 0,
				yisou INTEGER DEFAULT 0,
				mpcrawler INTEGER DEFAULT 0,
                duckduckgo INTEGER DEFAULT 0,
                bytes_flow INTEGER DEFAULT 0, 
                bing_flow INTEGER DEFAULT 0, 
                soso_flow INTEGER DEFAULT 0, 
                yahoo_flow INTEGER DEFAULT 0, 
                sogou_flow INTEGER DEFAULT 0, 
                google_flow INTEGER DEFAULT 0, 
                baidu_flow INTEGER DEFAULT 0, 
                qh360_flow INTEGER DEFAULT 0, 
                youdao_flow INTEGER DEFAULT 0, 
                yandex_flow INTEGER DEFAULT 0, 
                dnspod_flow INTEGER DEFAULT 0, 
                yisou_flow INTEGER DEFAULT 0, 
                other_flow INTEGER DEFAULT 0, 
                mpcrawler_flow INTEGER DEFAULT 0, 
                duckduckgo_flow INTEGER DEFAULT 0,
				other INTEGER DEFAULT 0
			)]]

		local sql_str1 = [[
			CREATE TABLE uri_stat (
				uri_md5 CHAR(32) PRIMARY KEY,
				uri TEXT,
				day1 INTEGER DEFAULT 0,
				day2 INTEGER DEFAULT 0,
				day3 INTEGER DEFAULT 0,
				day4 INTEGER DEFAULT 0,
				day5 INTEGER DEFAULT 0,
				day6 INTEGER DEFAULT 0,
				day7 INTEGER DEFAULT 0,
				day8 INTEGER DEFAULT 0,
				day9 INTEGER DEFAULT 0,
				day10 INTEGER DEFAULT 0,
				day11 INTEGER DEFAULT 0,
				day12 INTEGER DEFAULT 0,
				day13 INTEGER DEFAULT 0,
				day14 INTEGER DEFAULT 0,
				day15 INTEGER DEFAULT 0,
				day16 INTEGER DEFAULT 0,
				day17 INTEGER DEFAULT 0,
				day18 INTEGER DEFAULT 0,
				day19 INTEGER DEFAULT 0,
				day20 INTEGER DEFAULT 0,
				day21 INTEGER DEFAULT 0,
				day22 INTEGER DEFAULT 0,
				day23 INTEGER DEFAULT 0,
				day24 INTEGER DEFAULT 0,
				day25 INTEGER DEFAULT 0,
				day26 INTEGER DEFAULT 0,
				day27 INTEGER DEFAULT 0,
				day28 INTEGER DEFAULT 0,
				day29 INTEGER DEFAULT 0,
				day30 INTEGER DEFAULT 0,
				day31 INTEGER DEFAULT 0,
				day32 INTEGER DEFAULT 0
			)]]
		status, errorString = db:exec(sql_str1)	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow2 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow3 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow4 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow5 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow6 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow7 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow8 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow9 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow10 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow11 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow12 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow13 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow14 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow15 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow16 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow17 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow18 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow19 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow20 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow21 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow22 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow23 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow24 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow25 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow26 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow27 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow28 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow29 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow30 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow31 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow2 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow3 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow4 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow5 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow6 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow7 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow8 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow9 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow10 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow11 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow12 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow13 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow14 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow15 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow16 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow17 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow18 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow19 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow20 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow21 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow22 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow23 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow24 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow25 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow26 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow27 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow28 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow29 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow30 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow31 INTEGER DEFAULT 0;")	

		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN day_hour1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN flow_hour1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE uri_stat ADD COLUMN spider_flow_hour1 INTEGER DEFAULT 0;")	

		-- debug("Init db status:"..tostring(status))
		-- debug("Init db error:"..tostring(errorString))

		local sql_str1 = [[
			CREATE TABLE ip_stat (
				ip CHAR(15) PRIMARY KEY,
				area CHAR(8) DEFAULT "",
				day1 INTEGER DEFAULT 0,
				day2 INTEGER DEFAULT 0,
				day3 INTEGER DEFAULT 0,
				day4 INTEGER DEFAULT 0,
				day5 INTEGER DEFAULT 0,
				day6 INTEGER DEFAULT 0,
				day7 INTEGER DEFAULT 0,
				day8 INTEGER DEFAULT 0,
				day9 INTEGER DEFAULT 0,
				day10 INTEGER DEFAULT 0,
				day11 INTEGER DEFAULT 0,
				day12 INTEGER DEFAULT 0,
				day13 INTEGER DEFAULT 0,
				day14 INTEGER DEFAULT 0,
				day15 INTEGER DEFAULT 0,
				day16 INTEGER DEFAULT 0,
				day17 INTEGER DEFAULT 0,
				day18 INTEGER DEFAULT 0,
				day19 INTEGER DEFAULT 0,
				day20 INTEGER DEFAULT 0,
				day21 INTEGER DEFAULT 0,
				day22 INTEGER DEFAULT 0,
				day23 INTEGER DEFAULT 0,
				day24 INTEGER DEFAULT 0,
				day25 INTEGER DEFAULT 0,
				day26 INTEGER DEFAULT 0,
				day27 INTEGER DEFAULT 0,
				day28 INTEGER DEFAULT 0,
				day29 INTEGER DEFAULT 0,
				day30 INTEGER DEFAULT 0,
				day31 INTEGER DEFAULT 0,
				day32 INTEGER DEFAULT 0
			)]]
		status,errorString = db:exec(sql_str1)
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow2 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow3 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow4 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow5 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow6 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow7 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow8 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow9 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow10 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow11 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow12 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow13 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow14 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow15 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow16 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow17 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow18 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow19 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow20 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow21 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow22 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow23 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow24 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow25 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow26 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow27 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow28 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow29 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow30 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow31 INTEGER DEFAULT 0;")	

		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN day_hour1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE ip_stat ADD COLUMN flow_hour1 INTEGER DEFAULT 0;")	
		-- debug("Init ip_stat status:"..tostring(status))
		-- debug("Init ip_stat error:"..tostring(errorString))

		local sql_str_referer = [[
			CREATE TABLE referer2_stat (
				referer_md5 CHAR(32) PRIMARY KEY,
				referer TEXT,
				day1 INTEGER DEFAULT 0,
				day2 INTEGER DEFAULT 0,
				day3 INTEGER DEFAULT 0,
				day4 INTEGER DEFAULT 0,
				day5 INTEGER DEFAULT 0,
				day6 INTEGER DEFAULT 0,
				day7 INTEGER DEFAULT 0,
				day8 INTEGER DEFAULT 0,
				day9 INTEGER DEFAULT 0,
				day10 INTEGER DEFAULT 0,
				day11 INTEGER DEFAULT 0,
				day12 INTEGER DEFAULT 0,
				day13 INTEGER DEFAULT 0,
				day14 INTEGER DEFAULT 0,
				day15 INTEGER DEFAULT 0,
				day16 INTEGER DEFAULT 0,
				day17 INTEGER DEFAULT 0,
				day18 INTEGER DEFAULT 0,
				day19 INTEGER DEFAULT 0,
				day20 INTEGER DEFAULT 0,
				day21 INTEGER DEFAULT 0,
				day22 INTEGER DEFAULT 0,
				day23 INTEGER DEFAULT 0,
				day24 INTEGER DEFAULT 0,
				day25 INTEGER DEFAULT 0,
				day26 INTEGER DEFAULT 0,
				day27 INTEGER DEFAULT 0,
				day28 INTEGER DEFAULT 0,
				day29 INTEGER DEFAULT 0,
				day30 INTEGER DEFAULT 0,
				day31 INTEGER DEFAULT 0,
				day32 INTEGER DEFAULT 0
			)]]
		status,errorString = db:exec(sql_str_referer)
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow2 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow3 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow4 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow5 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow6 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow7 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow8 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow9 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow10 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow11 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow12 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow13 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow14 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow15 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow16 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow17 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow18 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow19 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow20 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow21 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow22 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow23 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow24 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow25 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow26 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow27 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow28 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow29 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow30 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow31 INTEGER DEFAULT 0;")	

		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN day_hour1 INTEGER DEFAULT 0;")	
		status, errorString = db:exec("ALTER TABLE referer2_stat ADD COLUMN flow_hour1 INTEGER DEFAULT 0;")	
		
		cache:set(db_path, true)
	end

	if db and db:isopen() then
		db:close()
	end
	return true
end

local function init_logs_db(log_dir, server_name, db_name)
	-- 初始化日志db
	local path = log_dir .. "/" .. server_name
	if not check_dir(path) then 
		res = create_dir(path, server_name) 
		if not res then
			return false
		end
		-- debug("create dir res:"..tostring(res))
	end
	local db_path = path .. "/" .. db_name
	if cache:get(db_path) then
		return
	end
	local db = sqlite3.open(db_path)
	local stmt = nil
	local rows = 0
	if db then
		local table_name = "site_logs"
		stmt = db:prepare("SELECT COUNT(*) FROM sqlite_master where type='table' and name=?")
		if stmt ~= nil then
			stmt:bind_values(table_name)
			stmt:step()
			rows = stmt:get_uvalues()
			stmt:finalize()
		end
	else
		return false
	end
	if stmt ~= nil and rows >0 then
		cache:set(db_path, true)
	else
		status, errorString = db:exec([[PRAGMA synchronous = 0]])
		status, errorString = db:exec([[PRAGMA page_size = 4096]])
		status, errorString = db:exec([[PRAGMA journal_mode = wal]])
		status, errorString = db:exec([[PRAGMA journal_size_limit = 1073741824]])
		status,errorString = db:exec[[
			CREATE TABLE site_logs (
				time INTEGER,
				ip TEXT,
				domain TEXT,
				server_name TEXT,
				method TEXT,
				status_code INTEGER,
				uri TEXT,
				body_length INTEGER,
				referer TEXT DEFAULT "",
				user_agent TEXT,
				is_spider INTEGER DEFAULT 0,
				protocol TEXT,
				request_time INTEGER,
				request_headers TEXT DEFAULT "",
				ip_list TEXT DEFAULT "",
				client_port INTEGER DEFAULT -1
			)]]
		status, errorString = db:exec([[CREATE INDEX time_inx ON site_logs(time)]])

		cache:set(db_path, true)
		-- ngx.log(ngx.INFO, "初始化日志数据库完成。")
		-- print(status, errorString)
	-- else
		-- ngx.log(ngx.INFO, "db 已存在。")
	end

	if db and db:isopen() then
		db:close()
	end
	return true
end

local function is_storing(name)
	local store_status = cache:get(name.."_STORING")
	if store_status ~= nil and store_status == true then
		return true 
	end
	return false
end

local function get_end_time()
	local s_time = os.time()
	local n_date = os.date("*t",s_time + 86400)
	n_date.hour = 0
	n_date.min = 0
	n_date.sec = 0
	d_time = os.time(n_date)
	return d_time - s_time
end

local function get_data_on(filename)
	local data = cache:get(filename)
	if not data then
		data = read_file_body_bylog(filename)
		if not data then
			data = {}
		else
			data = json.decode(data)
		end
	else
		data = json.decode(data)
	end
	return data
end

local function save_data_on(filename,data)
	local newdata = json.encode(data)
	local extime = 0;
	if string_find(filename,"%d+-%d+-%d+") then extime = 88400 end
	cache:set(filename,newdata,extime)
	if not cache:get(filename..'_lock') then
		cache:set(filename..'_lock',1,5)
		write_file_bylog(filename,newdata,'wb')
	end
end

local function get_clients()
-- local clients_json = cpath .. '/config/clients.json'
-- local clients = get_data_on(clients_json)
	return require "clients"
end

local function match_pc_client(ua, clients)
	local msie_pattern = nil
	local safari_pattern = nil
	local chrome_pattern = nil
	for column, pattern in pairs(clients) do
		if column == "safari" then 
			safari_pattern = pattern
		elseif column == "chrome" then 
			chrome_pattern = pattern 
		elseif column == "msie" then 
			msie_pattern = pattern
		elseif ngx_re_match(ua, pattern, "jo") then
			return column
		end
	end
	if msie_pattern and ngx_re.match(ua, msie_pattern, "jo") then 
		return "msie"
	end
	if chrome_pattern and ngx_re_match(ua, chrome_pattern, "jo") then
		return "chrome"
	end
	if safari_pattern and ngx_re_match(ua, safari_pattern, "jo") then
		return "safari"
	end
	return nil
end

local function match_norepeat_client(ua, clients)
	if clients == nil then return end
	for column, pattern in pairs(clients) do
		if ngx_re_match(ua, pattern, "jo") then
			return column
		end
	end
end

local function get_update_field(field, value)
	return field.."="..field.."+"..tostring(value)
end

local function match_client(ua)
    local uri_client_type_list = {}
	-- 匹配客户端
	local client_stat_fields = ""
	local clients_map = {
    	["android"] = "android",
    	["iphone"] = "iphone",
    	["ipod"] = "iphone",
    	["ipad"] = "iphone",
		["firefox"] = "firefox",
    	["msie"] = "msie",
    	["trident"] = "msie",
    	["360se"] = "qh360",
    	["360ee"] = "qh360",
    	["360browser"] = "qh360",
    	["qihoo"] = "qh360",
    	["the world"] = "theworld",
    	["theworld"] = "theworld",
    	["tencenttraveler"] = "tt",
    	["maxthon"] = "maxthon",
    	["opera"] = "opera",
    	["qqbrowser"] = "qq",
    	["ucweb"] = "uc",
    	["ubrowser"] = "uc",
    	["safari"] = "safari",
    	["chrome"] = "chrome",
    	["metasr"] = "metasr",
    	["2345explorer"] = "pc2345",
    	["edge"] = "edeg",
    	["edg"] = "edeg",
		["windows"] = "windows",
    	["linux"] = "linux",
    	["macintosh"] = "mac",
		["mobile"] = "mobile"
	}
	local mobile_regx = "(Mobile|Android|iPhone|iPod|iPad)"
	local mobile_res = ngx_re_match(ua, mobile_regx, "ijo")
	--mobile
	if mobile_res then
		client_stat_fields = client_stat_fields..","..get_update_field("mobile", 1)
		mobile_res = string_lower(mobile_res[0])
		if mobile_res ~= "mobile" then
			client_stat_fields = client_stat_fields..","..get_update_field(clients_map[mobile_res], 1)
		end
	else
		--pc
		-- 匹配结果的顺序，与ua中关键词的顺序有关
		-- lua的正则不支持|语法
		-- 短字符串string_find效率要比ngx正则高
		local pc_regx1 = "(360SE|360EE|360browser|Qihoo|TheWorld|TencentTraveler|Maxthon|Opera|QQBrowser|UCWEB|UBrowser|MetaSr|2345Explorer|Edg[e]*)" 
		local pc_res = ngx_re_match(ua, pc_regx1, "ijo")
		local cls_pc = nil
		if not pc_res then
			if string_find(ua, "[Ff]irefox") then
				cls_pc = "firefox"
			elseif string_find(ua, "MSIE") or string_find(ua, "Trident") then
				cls_pc = "msie"
			elseif string_find(ua, "[Cc]hrome") then
				cls_pc = "chrome"
			elseif string_find(ua, "[Ss]afari") then
				cls_pc = "safari"
			end
            table.insert(uri_client_type_list, clients_map[cls_pc])
		else
			cls_pc = string_lower(pc_res[0])
            if string_find(cls_pc, "[Ee]dg") then
                cls_pc = "edge"
            end
            table.insert(uri_client_type_list, cls_pc)
		end
		-- debug("UA:"..ua)
		-- debug("PC cls:"..tostring(cls_pc))
		if cls_pc then
			client_stat_fields = client_stat_fields..","..get_update_field(clients_map[cls_pc], 1)
		else
			-- machine and other
			local machine_res, err = ngx_re_match(ua, "([Cc]url|HeadlessChrome|[a-zA-Z]+[Bb]ot|[Ww]get|[Ss]pider|[Cc]rawler|[Ss]crapy|zgrab|[Pp]ython|java)", "ijo")
			if machine_res then
				client_stat_fields = client_stat_fields..","..get_update_field("machine", 1)
                table.insert(uri_client_type_list, "machine")
			else
				-- 移动端+PC端+机器以外 归类到 其他
				client_stat_fields = client_stat_fields..","..get_update_field("other", 1)
                table.insert(uri_client_type_list, "other")
			end
		end

		local os_regx = "(Windows|Linux|Macintosh)"
		local os_res = ngx_re_match(ua, os_regx, "ijo")
		if os_res then
			os_res = string_lower(os_res[0])
			client_stat_fields = client_stat_fields..","..get_update_field(clients_map[os_res], 1)
            table.insert(uri_client_type_list, clients_map[os_res])
		end
	end

	local other_regx = "MicroMessenger"
	local other_res = string_find(ua, other_regx)
	if other_res then
		client_stat_fields = client_stat_fields..","..get_update_field("weixin", 1)
        table.insert(uri_client_type_list, "weixin")
	end
	if client_stat_fields then
		client_stat_fields = string.sub(client_stat_fields, 2)
	end
    return client_stat_fields, uri_client_type_list
end

local function get_spiders()
	local spiders = require "spiders"
	return spiders
end

function get_spider_json(sfile_name, from_cache)
	-- 读取蜘蛛IP库并缓存
	local cache_key = cpath..sfile_name..'SPIDER'
	if from_cache then
		local cache_data = cache:get(cache_key)
		if cache_data then 
			return cache_data 
		end
	end
	data = read_file_body_bylog(cpath.."xspiders/"..sfile_name..'.json')
 	-- if not data then 
	-- 	data={}
	-- end 
	-- cache:set(cache_key,data, SEVEN_DAY_TIMEOUT)
	return data
end

function check_spider(name,ip)
	-- 验证蜘蛛真假
	-- name: 蜘蛛IP库分类名称
	-- ip: 请求IP
	-- @return: true代表真蜘蛛或者无法验证的蜘蛛；false代表假蜘蛛
	name = tostring(name)
	data=get_spider_json(name)
	if not data then
		return true
	end
	local ok,zhizhu_list_data = pcall(function()
		return json.decode(data)
	end)
	if not ok then
    	return true
	end
	spiders_key = "SPIDERS_"..name
	sp_key = "SPIDER_"..ip
    --debug("spiders_key: " .. tostring(spiders_key))
    --debug("sp_key: " .. tostring(sp_key))
	if cache:get(spiders_key) then
    	if cache:get(sp_key) then
            --debug("缓存了sp_key")
        	return true
    	end
        --debug("第一个false")
    -- 	return false
	end

	if not cache:get(spiders_key) then
	    cache:set(spiders_key,'1',86400)
    end

	for _,k in ipairs(zhizhu_list_data)
	do
        --if k == ip then
        --    debug("匹配到蜘蛛IP: " .. tostring(ip))
        --end
    	cache:set("SPIDER_"..k,'1',86400)
	end
	if cache:get(sp_key) then
        --debug("没有缓存sp_key，已经重新获取并缓存")
    	return true
	end
    --debug("第二个false")
	return false
end

local function match_spider_by_ip(client_ip)
	-- 通过蜘蛛IP库判断蜘蛛类型
	local sp_key = ip_spider_prefix..client_ip
	local zhizhu_ip_cache = cache:get(sp_key)
	
	if zhizhu_ip_cache then
		return true, zhizhu_ip_cache, spider_table[zhizhu_ip_cache]
	end
	return false, nil, 0
end

local function match_spider(client_ip)
	-- TODO 加入IP区间判断是否是蜘蛛请求
	-- 匹配蜘蛛请求
	
	local ua = ''
	if request_header['user-agent'] then
		ua = request_header['user-agent']
	end
	if not ua or type(ua) ~= "string" then
		return false, nil, 0
	end
	-- local spiders = get_spiders()
	local is_spider = false
	local spider_name = nil

	local res,err = ngx_re_match(ua, "(Baiduspider|Bytespider|360Spider|Sogou web spider|Sosospider|Googlebot|bingbot|AdsBot-Google|Google-Adwords|YoudaoBot|Yandex|DNSPod-Monitor|YisouSpider|mpcrawler)", "ijo")
	check_res = true
	if res then
		is_spider = true
		spider_match = string_lower(res[0])
		if string_find(spider_match, "baidu", 1, true) then
			spider_name = "baidu"
			check_res = check_spider("1", client_ip)
		elseif string_find(spider_match, "bytes", 1, true) then
			spider_name = "bytes"
			check_res = check_spider("7", client_ip)
		elseif string_find(spider_match, "360", 1, true) then
			spider_name = "qh360"
			check_res = check_spider("3", client_ip)
		elseif string_find(spider_match, "sogou", 1, true) then
			spider_name = "sogou"
			check_res = check_spider("4", client_ip)
		elseif string_find(spider_match, "soso", 1, true) then
			spider_name = "soso"
		elseif string_find(spider_match, "google", 1, true) then
			spider_name = "google"
			check_res = check_spider("2", client_ip)
		elseif string_find(spider_match, "bingbot", 1, true) then
			spider_name = "bing"
			check_res = check_spider("6", client_ip)
		elseif string_find(spider_match, "youdao", 1, true) then
			spider_name = "youdao"
		elseif string_find(spider_match, "dnspod", 1, true) then
			spider_name = "dnspod"
		elseif string_find(spider_match, "yandex", 1, true) then
			spider_name = "yandex"
		elseif string_find(spider_match, "yisou", 1, true) then
			spider_name = "yisou"
		elseif string_find(spider_match, "mpcrawler", 1, true) then
			spider_name = "mpcrawler"
		end
	end

	if is_spider then 
		if not check_res then
			return is_spider, spider_name, fake_spider
		end
		return is_spider, spider_name, spider_table[spider_name]
	end
	-- Curl|Yahoo|HeadlessChrome|包含bot|Wget|Spider|Crawler|Scrapy|zgrab|python|java|Adsbot|DuckDuckGo
	local other_res, err = ngx_re_match(ua, "(Yahoo|Slurp|DuckDuckGo)", "ijo")
	if other_res then
		other_res = string_lower(other_res[0])
		if string_find(other_res, "yahoo", 1, true) then
			spider_name = "yahoo"
			check_res = check_spider("5", client_ip)
		elseif string_find(other_res, "slurp", 1, true) then
			spider_name = "yahoo"
		elseif string_find(other_res, "duckduckgo", 1, true) then
			spider_name = "duckduckgo"
		end
		-- debug("Other Spider:"..other_res[0].."/User Agent:"..tostring(ua))
		if not check_res then
			return true, spider_name, fake_spider
		end
		return true, spider_name, spider_table[spider_name]
	end
	return false, nil, 0
end

local function statistics_ipc()
    -- 判断IP是否重复的时间限定范围是请求的当前时间+24小时
    local ipc = 0
    local uri_ipc = 0
    local ip_token = server_name .. '_' .. ip
    local uri_ip_token = server_name .. '_' .. ip .. '_' .. uri
    if not cache:get(ip_token) then
        ipc = 1
        cache:set(ip_token, 1, get_end_time())
    end

    if not cache:get(uri_ip_token) then
        uri_ipc = 1
        cache:set(uri_ip_token, 1, get_end_time())
    end
    return ipc, uri_ipc
end

local function statistics_request()
    -- 计算pv uv
    local pvc = 0
    local uvc = 0
    local uri_uvc = 0

    if not is_spider and method == 'GET' and status_code == 200 and body_length > 512 then
        local ua = ''
        if request_header['user-agent'] then
            ua = string_lower(request_header['user-agent'])
        end

        out_header = ngx.resp.get_headers()
        if out_header['content-type'] then
            if string_find(out_header['content-type'], 'text/html', 1, true) then
                pvc = 1
                if request_header['user-agent'] then
                    if string_find(ua, 'mozilla') then
                        local today2 = os.date("%Y-%m-%d")
                        local uv_token = ngx.md5(ip .. request_header['user-agent'] .. today2 .. server_name)
                        if not cache:get(uv_token) then
                            uvc = 1
                            cache:set(uv_token, 1, get_end_time())
                        end

                        local uri_uv_token = ngx.md5(ip .. request_header['user-agent'] .. today2 .. server_name .. uri)
                        if not cache:get(uri_uv_token) then
                            uri_uvc = 1
                            cache:set(uri_uv_token, 1, get_end_time())
                        end
                    end
                end
            end
        end
    end
    return pvc, uvc, uri_uvc
end

local function total_flow()
	local flow_key = server_name .. '_flow'
	local flow_write = server_name .. '_flow_write'
	if cache:get(flow_write) then
		cache:incr(flow_key,body_length)
	else
		local write_time = ngx.now()
		local now_flow = cache:get(flow_key)
		if not now_flow then now_flow = 0 end
		now_flow = now_flow + body_length
		local realtime_data = tostring(now_flow)..","..tostring(write_time)

		local queue_length = 10
		local position_key = flow_key.."_positon"
		local queue_key = flow_key.."_queue_"

		local req_position = cache:incr(position_key, 1, 0)
		cache:set(queue_key..tostring(req_position), realtime_data)

		local data = ""
		for i=1, queue_length, 1 do
			local _d = cache:get(queue_key..tostring(i))
			if _d ~= nil then
				-- ngx.log(ngx.INFO, "------------------Realtime Req Queue:"..tostring(i).."/data:".._d.."----------------------------")
				data = data.."\n".._d 
			end
		end

		local path = cpath .. '/logs/' .. server_name
		if not check_dir(path) then 
			local create_res = create_dir(path, server_name) 
			if not create_res then
				return false
			end
		end
		local filename = path .. '/flow_sec.json'
		write_file_bylog(filename,tostring(data),'wb+')

		if req_position == queue_length then
			cache:set(position_key, 0)
		end

		cache:set(flow_key,body_length,2)
		cache:set(flow_write,1,1)
	end
end

local function total_req_sec()
	local _key = server_name .. '_req'
	local _write = server_name .. '_req_write'
	if cache:get(_write) then
		cache:incr(_key,1)
	else
		ngx.update_time()
		local write_time = ngx.now()
		local now_ = cache:get(_key)
		if not now_ then now_ = 0 end
		now_ = now_ + 1
		local realtime_data = tostring(now_)..","..tostring(write_time)

		local queue_length = 10
		local position_key = _key.."_positon"
		local queue_key = _key.."_queue_"
		local req_position = cache:incr(position_key, 1, 0)
		-- ngx.log(ngx.INFO, "------------------Realtime Req Position:"..tostring(req_position).."----------------------------")
		cache:set(queue_key..tostring(req_position), realtime_data)
		local data = ""
		for i=1, queue_length, 1 do
			local _d = cache:get(queue_key..tostring(i))
			if _d ~= nil then
				-- ngx.log(ngx.INFO, "------------------Realtime Req Queue:"..tostring(i).."/data:".._d.."----------------------------")
				data = data.."\n".._d 
			end
		end

		local path = cpath .. 'logs/' .. server_name
		if not check_dir(path) then 
			local create_res = create_dir(path, server_name) 
			if not create_res then
				return false
			end
		end
		local filename = path .. '/req_sec.json'
		local write_res = write_file_bylog(filename,data,'wb+')

		if req_position == queue_length then
			cache:set(position_key, 0)
		end
		cache:set(_key,1,2)
		cache:set(_write,1,1)
	end
end

local function load_global_exclude_ip()
	-- 全局的排除IP规则缓存设置和更新
	local log_dir = cpath .. 'logs'
	local global_exclude_file = log_dir.."/reload_exclude_ip.pl"
	local load_key = "GLOBAL_EXCLUDE_IP_LOADED"
	if not file_exists(global_exclude_file) then 
		if cache:get(load_key) then
        	-- debug("Global not need to reload exclude ips.")
        	return true
    	end
	end

	local info_obj = package.loaded["total_config"]
	if info_obj then
		package.loaded["total_config"] = nil
		total_config = require "total_config"
	end

	local global_old_exclude_ip = total_config["global"]["old_exclude_ip"]
	-- debug("global old exclude ip:" ..tostring(global_old_exclude_ip))
	if global_old_exclude_ip then
		for k, _ip in pairs(global_old_exclude_ip)
		do
			-- debug("delete global old exclude ip: ".._ip)
			cache:delete("GLOBAL_EXCLUDE_IP_".._ip)
		end
	end

	-- 更新全局排除规则
	local global_exclude_ip = total_config["global"]["exclude_ip"]
	if global_exclude_ip then
		for i, _ip in pairs(global_exclude_ip)
		do 
			-- global
			if not cache:get("GLOBAL_EXCLUDE_IP_".._ip) then
				-- debug("set global exclude ip: ".._ip)
				cache:set("GLOBAL_EXCLUDE_IP_".._ip, true)
			end
		end
	end

	-- 删除更新规则标志
	if file_exists(global_exclude_file) then
		os.execute("rm -rf "..global_exclude_file)
	end

	cache:set(load_key, true)
end

local function load_exclude_ip(server_name)
	-- 加载排除IP
	-- 两种情况下需要重新加载排除IP:
	-- 1. 插件端改了配置文件，在对应的目录生成reload_exclude_ip.pl文件标记需要重新加载。
	-- 2. Nginx重新启动，Key=EXCLUDE_IP_LOADED的缓存为空。
	local log_dir = cpath .. 'logs'
	local site_exclude_file = log_dir.."/"..server_name.."/reload_exclude_ip.pl"
	local load_key = server_name .. "_EXCLUDE_IP_LOADED"
	if not file_exists(site_exclude_file) then 
		if cache:get(load_key) then
        	-- debug("Not need to reload exclude ips.")
        	return true
    	end
	end

	local info_obj = package.loaded["total_config"]
	if info_obj then
		package.loaded["total_config"] = nil
		total_config = require "total_config"
	end

	local site_config = total_config[server_name]
	local site_old_exclude_ip = nil
	if site_config then
		site_old_exclude_ip = site_config["old_exclude_ip"]
	end
	if site_old_exclude_ip then
		-- 加载站点的排除规则
		for k, _ip in pairs(site_old_exclude_ip)
		do
			-- debug("delete old exclude ip: ".._ip)
			cache:delete(server_name .. "_EXCLUDE_IP_".._ip)
			-- cache:delete("GLOBAL_EXCLUDE_IP_".._ip)
		end
	end
	local site_exclude_ip = nil
	if site_config then
		site_exclude_ip = site_config["exclude_ip"]
	end
	if site_exclude_ip then
		for i, _ip in pairs(site_exclude_ip)
		do 
			-- debug("set exclude ip: ".._ip)
			cache:set(server_name .. "_EXCLUDE_IP_".._ip, true)
		end
	end

	-- 删除更新规则标志
	if file_exists(site_exclude_file) then
		os.execute("rm -rf "..site_exclude_file)
	end

	-- set tag
	cache:set(load_key, true)

	return true
end

local function exclude_ip(ip)
	-- 排除IP匹配，分网站单独的配置和全局配置两种方式
	if config["exclude_ip"] then
		if config["exclude_ip"][ip] then
			-- ngx.log(ngx.ERR, "Exclude ip request: "..ip)
			return true
		end
	end
	return false
	
end

local function exclude_url(uri)
	if not uri then return false end
	if uri == "/" then return false end
	local url_conf = config["exclude_url"]
	if not url_conf then return false end
	local sub_uri = string.sub(uri, 2)
	for i,conf in pairs(url_conf)
	do
		local mode = conf["mode"]
		local url = conf["url"]
		-- ngx.log(ngx.ERR, "Match ("..mode..") "..the_uri .." VS "..url)
		if mode == "regular" then
			if ngx_re_find(uri, url, "ijo") then
				-- debug("exclude url:"..uri.." match by:"..url)
				return true
			end
		else
			if uri == url or sub_uri == url then
				return true
			end
		end
	end
	return false
end

local function get_suffix(uri)
	if not uri then return nil end
	local s, e = ngx_re_find(uri, "[.][^.]+$")
	if s then
		return string_sub(uri, s+1, e)
	end
	return nil
end

local function exclude_extension(uri)
	if not uri then return false end
	local ex_conf = config['exclude_extension']
	if not ex_conf then return false end
	local suffix = get_suffix(uri)
	if not suffix then return false end
	if ex_conf[suffix] then
		-- ngx.log(ngx.ERR, "Exclude extension request: "..suffix)
		return true
	end
	return false
end

local function exclude_status(res_status_code)
	if not config['exclude_status'] then return false end
	local str_status_code = tostring(res_status_code)
	if config['exclude_status'][str_status_code] then
		-- ngx.log(ngx.ERR, "Exclude reponse status code: "..res_status_code)
		return true
	end
	return false
end

local function get_store_key()
	return os.date("%Y%m%d%H", os.time())
end


local function load_update_hour(update_server_name)
	local _file = cpath.."logs/"..update_server_name.."/update_hour.log"
	local cache_val = cache:get(_file)
	if cache_val then
		-- debug("load update day from cache: "..cache_val)
		return cache_val
	end
	local val = read_file_body_bylog(_file)
	if not val then
		-- 处理未读取到记录的情况
		val = hour_str
	end
	cache:set(_file, val, 7200)
	return val
end

local function load_update_day(update_server_name)
	local _file = cpath.."logs/"..update_server_name.."/update_day.log"
	local cache_val = cache:get(_file)
	if cache_val then
		-- debug("load update day from cache: "..cache_val)
		return cache_val
	end
	local val = read_file_body_bylog(_file)
	if not val then
		-- 处理未读取到记录的情况
		val = today
	end
	cache:set(_file, val, ONE_DAY_TIMEOUT)
	return val
end

local function write_update_hour(update_server_name)
	local update_hour = tostring(hour_str)
	local _file = cpath.."logs/"..update_server_name.."/update_hour.log"
	write_file_bylog(_file, update_hour, "w")
	cache:set(_file, update_hour, ONE_DAY_TIMEOUT)
end

local function write_update_day(update_server_name)
	local update_day = tostring(today)
	local _file = cpath.."logs/"..update_server_name.."/update_day.log"
	write_file_bylog(_file, update_day, "w")
	cache:set(_file, update_day, ONE_DAY_TIMEOUT)
end

local function statistics_uri(db, stat_server_name, uri, uri_md5, body_length, is_spider)
	-- 统计uri请求次数和流量
	local open_statistics_uri = site_config["statistics_uri"]
	if not open_statistics_uri then return true end

	local stat_sql = nil
	stat_sql = "INSERT INTO uri_stat(uri_md5,uri) SELECT \""..uri_md5.."\",\""..uri.."\" WHERE NOT EXISTS (SELECT uri_md5 FROM uri_stat WHERE uri_md5=\""..uri_md5.."\");"
	local res, err = db:exec(stat_sql)

	if not is_spider then
		is_spider = 0
	end

	-- debug("is spider?:"..tostring(is_spider))
	if is_spider > 0 and is_spider ~= fake_spider then
		-- debug("statistcs spider flow:"..uri)
		local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..spider_hour1_column.."="..spider_hour1_column.."+"..body_length
		stat_sql = "UPDATE uri_stat SET "..day_column.."="..day_column.."+1,"..spider_column.."="..spider_column.."+"..body_length..hour_update_sql.." WHERE uri_md5=\""..uri_md5.."\""
	else
		local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..flow_hour1_column.."="..flow_hour1_column.."+"..body_length
		stat_sql = "UPDATE uri_stat SET "..day_column.."="..day_column.."+1,"..flow_column.."="..flow_column.."+"..body_length..hour_update_sql.." WHERE uri_md5=\""..uri_md5.."\""
	end
	local res, err = db:exec(stat_sql)
	-- debug("uri:"..tostring(uri))
	-- debug("uri stat res:"..tostring(res))
	return true
end

local function get_uri_access_uri_id(db, uri)
    -- uri独立统计：获取指定uri的uri_id
    local select_sql1 = nil
    local tableExists = false
    select_sql1 = "SELECT name FROM sqlite_master WHERE type='table';"
    for row in db:nrows(select_sql1) do
        if tostring(row.name) == "uri_access" then
            tableExists = true
            break
        end
    end
    if not tableExists then
        return nil
    end

    --debug("row: --> " .. uri)
    select_sql1 = "SELECT id,uri FROM uri_access;"
    for row in db:nrows(select_sql1) do
        if uri == tostring(row.uri) then
            --debug("uri id: --> " .. tostring(row.id))
            --debug("res uri: --> " .. tostring(row.uri))
            return row.id
        end
    end
end

local function statistics_uri_count(db, uri_id, is_spider, uri_count_request_dict, local_date_dict)
    -- uri独立统计：统计独立uri请求次数和流量
    local table_name = "uri_count_stat_" .. local_date_dict["local_date_year_month"]
    if uri_count_request_dict == nil then
        return true
    end

    if uri_id then
        --debug("uri_id: " .. tostring(uri_id))
        local uri_count_dict = {}
        local count_type_list = {"pv", "uv", "ip", "spider"}

        if not is_spider then
            is_spider = 0
        end

        if uri_count_request_dict["uri_count_pv"] > 0 then
            uri_count_dict["pv"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        end
        if uri_count_request_dict["uri_count_uv"] > 0 then
            uri_count_dict["uv"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        end
        if uri_count_request_dict["uri_count_ip"] > 0 then
            uri_count_dict["ip"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        end
        if is_spider > 0 and is_spider ~= fake_spider then
            uri_count_dict["spider"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        end

        local stmt, err = db:prepare(string.format("INSERT INTO %s(uri_id, date, count_type) SELECT :uri_id, :date, :count_type WHERE NOT EXISTS (SELECT uri_id, date, count_type FROM %s WHERE uri_id=:uri_id AND date=:date AND count_type=:count_type LIMIT 1);",table_name, table_name))

        for _, count_type in ipairs(count_type_list) do
            stmt:bind_names {
                uri_id = uri_id,
                date = local_date_dict["local_date_year_month_day"],
                count_type = count_type
            }
            stmt:step()
            stmt:reset()
        end
        stmt:finalize()


        for key, count_type in pairs(uri_count_dict) do
            if uri_count_dict[key] ~= nil then
                local update_sql = "UPDATE " .. table_name .. " SET " .. count_type .. " WHERE uri_id=" .. uri_id .. " AND date=" .. local_date_dict["local_date_year_month_day"] .. " AND count_type='" .. key .. "'"
                db:exec(update_sql)
            end
        end
    end
end

local function statistics_uri_client_stat(db, uri_id, uri_client_type_list, local_date_dict)
    -- uri独立统计：统计每个客户端的数量
    local table_name = "uri_client_stat_" .. local_date_dict["local_date_year_month"]
    if uri_id then

        local tmp_uri_client_stat_dict = {}
        if uri_client_type_list then
            for _, an_client in ipairs(uri_client_type_list) do
                tmp_uri_client_stat_dict[an_client] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
            end
        end

        local uri_client_list = {"weixin","android","iphone","mac","windows","other","mobil",
                                 "linux","edge","firefox","msie","metasr","qh360",
                                 "theworld","tt","maxthon","opera","qq","uc","pc2345","safari",
                                 "chrome","machine"}

        local stmt, err = db:prepare(string.format("INSERT INTO %s(uri_id, date, count_type) SELECT :uri_id, :date, :count_type WHERE NOT EXISTS (SELECT uri_id, date, count_type FROM %s WHERE uri_id=:uri_id AND date=:date AND count_type=:count_type LIMIT 1);",table_name, table_name))

        for _, count_type in ipairs(uri_client_list) do
            stmt:bind_names {
                uri_id = uri_id,
                date = local_date_dict["local_date_year_month_day"],
                count_type = count_type
            }
            stmt:step()
            stmt:reset()
        end
        stmt:finalize()

        for key, count_type in pairs(tmp_uri_client_stat_dict) do
            if tmp_uri_client_stat_dict[key] ~= nil then
                local update_sql = "UPDATE " .. table_name .. " SET " .. count_type .. " WHERE uri_id=" .. uri_id .. " AND  date=" .. local_date_dict["local_date_year_month_day"] .. " AND count_type='" .. key .. "'"
                db:exec(update_sql)
            end
        end
    end
end

local function statistics_uri_spider_stat(db, uri_id, uri_count_request_dict, local_date_dict)
    -- uri独立统计：统计每个蜘蛛的数量
    local table_name = "uri_spider_stat_" .. local_date_dict["local_date_year_month"]
    if uri_id then
        local tmp_uri_spider_stat = ""
        if uri_count_request_dict["uri_count_spider_type"] then
            tmp_uri_spider_stat = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        else
            return true
        end

        local uri_spider_list = {"bytes", "bing", "soso", "yahoo", "sogou", "google", "baidu",
                                "qh360", "youdao", "yandex", "dnspod", "yisou", "mpcrawler",
                                "duckduckgo", "other"}

        local stmt, err = db:prepare(string.format("INSERT INTO %s(uri_id, date, count_type) SELECT :uri_id, :date, :count_type WHERE NOT EXISTS (SELECT uri_id, date, count_type FROM %s WHERE uri_id=:uri_id AND date=:date AND count_type=:count_type LIMIT 1);",table_name, table_name))

        for _, count_type in ipairs(uri_spider_list) do
            stmt:bind_names {
                uri_id = uri_id,
                date = local_date_dict["local_date_year_month_day"],
                count_type = count_type
            }
            stmt:step()
            stmt:reset()
        end
        stmt:finalize()

        local update_sql = "UPDATE " .. table_name .. " SET " .. tmp_uri_spider_stat .. " WHERE uri_id=" .. uri_id .. " AND  date=" .. local_date_dict["local_date_year_month_day"] .. " AND count_type='" .. uri_count_request_dict["uri_count_spider_type"] .. "'"
        db:exec(update_sql)
    end
end

local function statistics_uri_ip_stat(db, uri_id, uri_count_request_dict, local_date_dict)
    -- uri独立统计：统计每个来访的ip
    local table_name = "uri_ip_stat_" .. local_date_dict["local_date_year_month"]
    if uri_id then
        local tmp_uri_ip_stat = ""
        if uri_count_request_dict["uri_count_ip_t"] then
            tmp_uri_ip_stat = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. " + 1"
        else
            return true
        end

        local stmt, err = db:prepare(string.format("INSERT INTO %s(uri_id, date, ip) SELECT :uri_id, :date, :ip WHERE NOT EXISTS (SELECT uri_id, date, ip FROM %s WHERE uri_id=:uri_id AND date=:date AND ip=:ip LIMIT 1);",table_name, table_name))

        stmt:bind_names {
            uri_id = uri_id,
            date = local_date_dict["local_date_year_month_day"],
            ip = uri_count_request_dict["uri_count_ip_t"]
        }
        stmt:step()
        stmt:reset()
        stmt:finalize()

        local update_sql = "UPDATE " .. table_name .. " SET " .. tmp_uri_ip_stat .. " WHERE uri_id=" .. uri_id .. " AND  date=" .. local_date_dict["local_date_year_month_day"] .. " AND ip='" .. uri_count_request_dict["uri_count_ip_t"] .. "'"
        db:exec(update_sql)
    end
end

local function statistics_uri_flow_stat(db, uri_id, is_spider, body_length, uri_count_request_dict, local_date_dict)
    -- uri独立统计：统计每个蜘蛛的数量
    local table_name = "uri_flow_stat_" .. local_date_dict["local_date_year_month"]
    if uri_id then
        local tmp_uri_flow_stat = {}

        tmp_uri_flow_stat["flow"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. "+" .. body_length
        if is_spider > 0 and is_spider ~= fake_spider then
            tmp_uri_flow_stat["spider_flow"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. "+" .. body_length
        end

        if uri_count_request_dict["uri_count_spider_type"] then
            tmp_uri_flow_stat[uri_count_request_dict["uri_count_spider_type"] .. "_flow"] = "h" .. local_date_dict["local_date_hour"] .. " = " .. "h" .. local_date_dict["local_date_hour"] .. "+" .. body_length
        end

        local uri_spider_list = {"flow", "spider_flow", "bytes_flow", "bing_flow", "soso_flow",
                              "yahoo_flow", "sogou_flow", "google_flow", "baidu_flow",
                              "qh360_flow", "youdao_flow", "yandex_flow", "dnspod_flow",
                              "yisou_flow", "other_flow", "mpcrawler_flow", "duckduckgo_flow"}

        local stmt, err = db:prepare(string.format("INSERT INTO %s(uri_id, date, count_type) SELECT :uri_id, :date, :count_type WHERE NOT EXISTS (SELECT uri_id, date, count_type FROM %s WHERE uri_id=:uri_id AND date=:date AND count_type=:count_type LIMIT 1);",table_name, table_name))

        for _, count_type in ipairs(uri_spider_list) do
            stmt:bind_names {
                uri_id = uri_id,
                date = local_date_dict["local_date_year_month_day"],
                count_type = count_type
            }
            stmt:step()
            stmt:reset()
        end
        stmt:finalize()

        for key, count_type in pairs(tmp_uri_flow_stat) do
            if tmp_uri_flow_stat[key] ~= nil then
                local update_sql = "UPDATE " .. table_name .. " SET " .. count_type .. " WHERE uri_id=" .. uri_id .. " AND  date=" .. local_date_dict["local_date_year_month_day"] .. " AND count_type='" .. key .. "'"
                db:exec(update_sql)
            end
        end
    end
end

local function statistics_referer(db, referer, referer_md5, body_length)
	local stat_sql = nil
	stat_sql = "INSERT INTO referer2_stat(referer, referer_md5) SELECT \""..referer.."\",\""..referer_md5.."\" WHERE NOT EXISTS (SELECT referer_md5 FROM referer2_stat WHERE referer_md5=\""..referer_md5.."\");"
	-- debug(stat_sql)
	local res, err = db:exec(stat_sql)
	local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..flow_hour1_column.."="..flow_hour1_column.."+"..body_length
	stat_sql = "UPDATE referer2_stat SET "..day_column.."="..day_column.."+1,"..flow_column.."="..flow_column.."+"..body_length..hour_update_sql.." WHERE referer_md5=\""..referer_md5.."\""
	local res, err = db:exec(stat_sql)
	-- debug("referer stat res:"..tostring(res))
	-- debug("referer stat err:"..tostring(err))
	return true
end

local function statistics_ip(db, stat_server_name, ip, body_length)
	local open_statistics_ip = site_config["statistics_ip"]	
	if not open_statistics_ip then return true end
	
	local stat_sql = nil
	stat_sql = "INSERT INTO ip_stat(ip) SELECT \""..ip.."\" WHERE NOT EXISTS (SELECT ip FROM ip_stat WHERE ip=\""..ip.."\");"
	local res, err = db:exec(stat_sql)
	local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..flow_hour1_column.."="..flow_hour1_column.."+"..body_length
	stat_sql = "UPDATE ip_stat SET "..day_column.."="..day_column.."+1,"..flow_column.."="..flow_column.."+"..body_length..hour_update_sql.." WHERE ip=\""..ip.."\""
	local res, err = db:exec(stat_sql)
	-- debug("ip stat res:"..tostring(res))
	-- debug("ip stat err:"..tostring(err))
	return true
end

local function update_stat(update_server_name, db, stat_table, key, columns)
	-- 根据指定表名，更新统计数据
	if not columns then return end
	local stmt, err = db:prepare(string.format("INSERT INTO %s(time) SELECT :time WHERE NOT EXISTS(SELECT time FROM %s WHERE time=:time);", stat_table, stat_table))
	if not stmt then
		return
	end
	stmt:bind_names{time=key}
	local res, err = stmt:step()
	stmt:finalize()
	local update_sql = "UPDATE ".. stat_table .. " SET " .. columns
	update_sql = update_sql .. " WHERE time=" .. key
	status, errorString = db:exec(update_sql)
end

local function get_domain()
	local domain = request_header['host']
	if domain ~= nil then
		domain = string.gsub(domain, "_", ".")
	else
		domain = "unknown"
	end
	return domain
end

local function cache_value(id, key, value)
	local line_id_key = "logline_"..server_name.."_"..id.."_"..key
	cache:set(line_id_key, value)
end

local function clear_value(store_server_name, id, key)
	local line_id_key = "logline_"..store_server_name.."_"..id.."_"..key
	cache:delete(line_id_key)
end

local function get_value(store_server_name, id, key)
	local line_id_key = "logline_"..store_server_name.."_"..id.."_"..key
	local value = cache:get(line_id_key)
	-- cache:delete(line_id_key)
	return value
end

-- 存储单行日志
local function store_line(total_db, stmt, store_server_name, lineno)

    local uri_count_request_dict
    local uri_client_type_list

    local uri_client_value = get_value(store_server_name, lineno, "uri_client_type_list")
    --debug("uri_client_value: " .. tostring(uri_client_value))

    local uri_count_value = get_value(store_server_name, lineno, "uri_count_request_dict")
    --debug("uri_count_value: " .. tostring(uri_count_value))

    if uri_client_value then
        uri_client_type_list = json.decode(uri_client_value)
    end

    if uri_count_value then
        uri_count_request_dict = json.decode(uri_count_value)
    end

    local logvalue = get_value(store_server_name, lineno, "logline")
    if not logvalue then
        return false
    end

    local logline = json.decode(logvalue)
    local time = logline["time"]
    local time_key = logline["time_key"]
    local ip = logline["ip"]
    local ip_list = logline["ip_list"]
    local domain = logline["domain"]
    local server_name = logline["server_name"]
    local real_server_name = logline["real_server_name"]
    local method = logline["method"]
    local status_code = logline["status_code"]
    local uri = logline["uri"]
    local request_uri = logline["request_uri"]
    local body_length = logline["body_length"]
    local referer = logline["referer"]
    local user_agent = logline["user_agent"]
    local protocol = logline["protocol"]
    local request_time = logline["request_time"]
    local is_spider = logline["is_spider"]
    local request_headers = logline["request_headers"]
    local excluded = logline["excluded"]
    local id = logline["id"]
    local client_port = logline["client_port"]
    if not client_port then
        client_port = -1
    end

    local request_stat_fields = nil
    local client_stat_fields = nil
    local spider_stat_fields = nil
    local stat_fields = get_value(store_server_name, id, "STAT_FIELDS")
    if stat_fields == nil then
        -- debug("Log stat fields is nil.")
        -- debug("Logdata:"..logvalue)
    else
        stat_fields = split_bylog(stat_fields, ";")
        request_stat_fields = stat_fields[1]
        client_stat_fields = stat_fields[2]
        spider_stat_fields = stat_fields[3]
        --debug("request_stat_fields: --> " .. request_stat_fields)
        --debug("client_stat_fields: --> " .. client_stat_fields)
        --debug("spider_stat_fields: --> " .. spider_stat_fields)

        if "x" == client_stat_fields then
            client_stat_fields = nil
        end

        if "x" == spider_stat_fields then
            spider_stat_fields = nil
        end
    end

    if not excluded then
        stmt:bind_names {
            time = time,
            ip = ip,
            domain = domain,
            server_name = real_server_name,
            method = method,
            status_code = status_code,
            uri = request_uri,
            body_length = body_length,
            referer = referer,
            user_agent = user_agent,
            protocol = protocol,
            request_time = request_time,
            is_spider = is_spider,
            request_headers = request_headers,
            ip_list = ip_list,
            client_port = client_port
        }
        local res, err = stmt:step()
        if tostring(res) == "5" then
            -- debug("Step数据库连接繁忙，稍候存储。")
            return false
        end
        stmt:reset()
        update_stat(store_server_name, total_db, "client_stat", time_key, client_stat_fields)
        update_stat(store_server_name, total_db, "spider_stat", time_key, spider_stat_fields)
        if referer and string_len(referer) > 0 then
            local in_site_check_res = ngx_re_match(referer, "^(http[s]*://)*" .. store_server_name)
            if not in_site_check_res then
                -- debug("--- from other site:"..referer.."/"..store_server_name)
                local new_referer, n, err = ngx_re_sub(referer, "\\?.*", "")
                if not new_referer then
                    new_referer = referer
                end
                -- debug("statistics referer: "..referer.."/simple referer:"..new_referer)
                statistics_referer(total_db, new_referer, ngx.md5(new_referer), body_length)
            end
        end

        local total_uri
        if not request_uri then
            total_uri = uri
        else
            total_uri = request_uri
        end
        if total_uri then
            local new_uri, n, err = ngx_re_sub(total_uri, "\\?.*", "")
            statistics_uri(total_db, store_server_name, new_uri, ngx.md5(new_uri), body_length, is_spider)
            local uri_id = get_uri_access_uri_id(total_db, total_uri)
            if uri_id then
                local local_date_dict = {
                    local_date_year_month_day = os.date("%Y%m%d"),
                    local_date_year_month = os.date("%Y%m"),
                    local_date_hour = os.date("%H")
                }

                statistics_uri_count(total_db, uri_id, is_spider, uri_count_request_dict, local_date_dict)
                statistics_uri_ip_stat(total_db, uri_id, uri_count_request_dict, local_date_dict)
                statistics_uri_client_stat(total_db, uri_id, uri_client_type_list, local_date_dict)
                statistics_uri_spider_stat(total_db, uri_id, uri_count_request_dict, local_date_dict)
                statistics_uri_flow_stat(total_db, uri_id, is_spider, body_length, uri_count_request_dict, local_date_dict)
            end
        end
        if ip then
            statistics_ip(total_db, store_server_name, ip, body_length)
        end
    end
    update_stat(store_server_name, total_db, "request_stat", time_key, request_stat_fields)
    return true
end

-- 存储指定站点的日志
local function store_logs(store_server_name)
    if is_migrating(store_server_name) == true then
        -- debug("Migrating...")
        return
    end
    local flush_data = false
    local waiting_store_key = store_server_name .. "_WAITING_STORE"
    local flush_data_key = store_server_name .. "_FLUSH_DATA"
    local cache_count_id_key = store_server_name .. "_CACHE_COUNT"
    local cache_count = cache:get(cache_count_id_key)
    if cache_count == nil then
        cache_count = 0
    end

    if not cache:get(waiting_store_key) or cache_count > cache_count_threshold then
        local x = "go"
    else
        if cache:get(flush_data_key) then
            flush_data = true
        else
            -- debug("Cache count:"..cache_count)
            -- debug("Waiting...")
            return
        end
    end

    if is_storing(store_server_name) then
        -- debug("其他worker正在存储中，稍候存储。")
        cache:delete(flush_data_key)
        return
    end

    today = os.date("%Y%m%d")
    day = os.date("%d")
    number_day = tonumber(day)
    day_column = "day" .. number_day
    flow_column = "flow" .. number_day
    spider_column = "spider_flow" .. number_day

    hour_str = os.date("%Y%m%d%H")

    local storing_key = store_server_name .. "_STORING"
    -- local worker_id = ngx.worker.id()
    cache:set(storing_key, true, 60)
    if flush_data == false then
        cache:set(waiting_store_key, ngx.now(), cache_interval_threshold)
    end
    cache:delete(flush_data_key)

    -- local store_start_time = gtime.get_msec()

    -- 1.计算存储数据区间段
    local last_insert_id_key = store_server_name .. "_LAST_INSERT_ID"
    local store_start_id_key = store_server_name .. "_STORE_START"
    local last_id = cache:get(last_insert_id_key)
    local store_start = cache:get(store_start_id_key)
    if store_start == nil then
        store_start = 1
    end
    local store_end = last_id
    if store_end == nil then
        store_end = 1
    end

    site_config = get_config(store_server_name)

    -- ngx.log(ngx.ERR, "--------------["..worker_id.."]开始存储"..tostring(is_storing()).."/"..tostring(cache:get("STORING")).."--------------------------")

    -- debug("--------------["..worker_id.."]开始存储"..tostring(is_storing()).."/"..tostring(cache:get("STORING")).."--------------------------")
    -- debug("Start:"..store_start.."/End:"..store_end)
    local store_count = 0

    local stmt2 = nil

    local log_dir = cpath .. 'logs'
    data_dir = site_config["data_dir"]
    if data_dir then
        log_dir = data_dir
    end
    local base_path = log_dir .. '/' .. store_server_name .. "/"

    local total_db_path = base_path .. total_db_name
    local logs_db_name = today .. ".db"
    local logs_db_path = base_path .. logs_db_name

    local logs_init_res = true
    local total_init_res = true
    -- debug("logs db path:"..tostring(logs_db_path))
    -- debug("total db path:"..tostring(total_db_path))
    if not cache:get(logs_db_path) then
        -- debug("to init by shared dict control.")
        logs_init_res = init_logs_db(log_dir, store_server_name, logs_db_name)
    end
    if not file_exists(logs_db_path) then
        -- debug("to init by file check.")
        cache:set(logs_db_path, nil)
        logs_init_res = init_logs_db(log_dir, store_server_name, logs_db_name)
    end

    if not cache:get(total_db_path) then
        total_init_res = init_total_db(log_dir, store_server_name, total_db_name)
    end
    if not file_exists(total_db_path) then
        cache:set(total_db_path, nil)
        total_init_res = init_total_db(log_dir, store_server_name, total_db_name)
    end
    if not logs_init_res or not total_init_res then
        -- debug("logs:"..tostring(logs_init_res))
        -- debug("total:"..tostring(total_init_res))
        -- debug("初始化数据库异常。")
        cache:set(storing_key, false)
        return false
    end

    local logs_db, err1 = sqlite3.open(logs_db_path)
    local total_db, err2 = sqlite3.open(total_db_path)
    -- debug("Open db:"..tostring(db))
    if logs_db ~= nil then
        stmt2 = logs_db:prepare [[INSERT INTO site_logs(
			time, ip, domain, server_name, method, status_code, uri, body_length,
			referer, user_agent, protocol, request_time, is_spider, request_headers, ip_list, client_port)
			VALUES(:time, :ip, :domain, :server_name, :method, :status_code, :uri,
			:body_length, :referer, :user_agent, :protocol, :request_time, :is_spider,
			:request_headers, :ip_list, :client_port)]]
    end

    if logs_db == nil or stmt2 == nil or total_db == nil then
        -- debug("网站监控报表数据库连接异常。")
        cache:set(storing_key, false)

        if total_db and total_db:isopen() then
            total_db:close()
        end
        if logs_db and logs_db:isopen() then
            logs_db:close()
        end
        return true
    end

    status, errorString = logs_db:exec([[BEGIN TRANSACTION]])
    status, errorString = total_db:exec([[BEGIN TRANSACTION]])

    local update_hour = load_update_hour(store_server_name)
    if not update_hour or tostring(update_hour) ~= tostring(hour_str) then
        -- reset
        local update_sql = "UPDATE uri_stat SET " .. day_hour1_column .. "=0," .. spider_hour1_column .. "=0," .. flow_hour1_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        update_sql = "UPDATE ip_stat SET " .. day_hour1_column .. "=0," .. flow_hour1_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        update_sql = "UPDATE referer2_stat SET " .. day_hour1_column .. "=0," .. flow_hour1_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        write_update_hour(store_server_name)
    end

    update_day = load_update_day(store_server_name)
    if not update_day or tostring(update_day) ~= tostring(today) then
        -- reset
        local update_sql = "UPDATE uri_stat SET " .. day_column .. "=0," .. spider_column .. "=0," .. flow_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        update_sql = "UPDATE ip_stat SET " .. day_column .. "=0," .. flow_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        update_sql = "UPDATE referer2_stat SET " .. day_column .. "=0," .. flow_column .. "=0"
        status, errorString = total_db:exec(update_sql)

        write_update_day(store_server_name)
    end
    -- local start_transaction_time = gtime.get_msec()
    if store_end >= store_start then
        for i = store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
                clear_value(store_server_name, i, "uri_count_request_dict")
                clear_value(store_server_name, i, "uri_client_type_list")
                -- if store_count >= cache_count_threshold then
                -- 	store_end = i
                -- 	break
                -- end
            end
        end
    else
        local _tmp_store_end = store_end
        store_end = max_log_id
        for i = store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
                clear_value(store_server_name, i, "uri_count_request_dict")
                clear_value(store_server_name, i, "uri_client_type_list")
            end
        end

        store_start = 1
        store_end = _tmp_store_end
        for i = store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
                clear_value(store_server_name, i, "uri_count_request_dict")
                clear_value(store_server_name, i, "uri_client_type_list")
            end
        end
    end

    local res, err = stmt2:finalize()
    if tostring(res) ~= "5" then
        local res, err = total_db:execute([[COMMIT]])
        local res, err = logs_db:execute([[COMMIT]])
        -- debug("Commit res:"..tostring(res))
        -- debug("Commit err:"..tostring(err))

        -- local end_clear = gtime.get_msec()
        -- debug("清理和提交事务耗时:"..tostring(end_clear-clear_start))
        cache:set(store_start_id_key, store_end)
        cache:incr(cache_count_id_key, tonumber(store_count) * -1)
        local cache_count = cache:get(cache_count_id_key)
        if not cache_count then
            cache_count = 0
        end
        if cache_count > cache_count_threshold or cache_count < 0 then
            cache:delete(cache_count_id_key)
        end
    end
    if total_db and total_db:isopen() then
        total_db:close()
    end
    if logs_db and logs_db:isopen() then
        logs_db:close()
    end
    cache:set(waiting_store_key, ngx.now(), cache_interval_threshold)
    -- local finish_time = gtime.get_msec()
    -- debug("-----------------------DEBUG: 存储总耗时:"..tostring(finish_time-store_start_time).."ms--------------------------")
    -- debug("Store count:"..tostring(store_count))
    cache:set(storing_key, false)
end


-- 缓存并且存储日志
local function cache_logs()

    -- local cache_start_time = gtime.get_msec()
    local excluded = false
    request_header = ngx_req.get_headers()
    ip = get_client_ip_bylog()
    local request_uri = ngx_var.request_uri
    excluded = exclude_status(status_code) or exclude_extension(uri) or exclude_url(request_uri) or exclude_ip(ip)

    domain = get_domain()
    method = ngx_req.get_method()
    if method == "" or not method then
        return false
    end
    -- ngx.log(ngx.ERR, "Header:")
    -- for k,v in pairs(request_header) do
    -- 	ngx.log(ngx.ERR, "-----------------"..k..":"..v.."--------------------")
    -- end
    ip_list = request_header["x-forwarded-for"]
    client_port = ngx_var.remote_port
    if ip and not ip_list then
        ip_list = ip
    end
    local remote_addr = ngx_var.remote_addr
    if not string_find(ip_list, remote_addr) then
        if remote_addr then
            ip_list = ip_list .. "," .. remote_addr
        end
    end
    -- ipn = arrip_bylog(ip)

    -- 缓存日志，只干塞缓存这一件事
    -- 记录从ngx启动以来生成的数据行id，进行累加
    local new_id = nil
    -- if cache:get("STORE_START") then
    -- end
    local last_insert_id_key = server_name .. "_LAST_INSERT_ID"
    local cache_count_id_key = server_name .. "_CACHE_COUNT"
    if not cache:get(server_name .. "_CLEAR_CACHE_COUNT") then
        cache:delete(server_name .. "_CACHE_COUNT")
        cache:set(server_name .. "_CLEAR_CACHE_COUNT", true)
        -- debug("Cleared cache count.")
    end
    local err = nil
    new_id, err = cache:incr(last_insert_id_key, 1, 0)
    cache:incr(cache_count_id_key, 1, 0)
    if new_id >= max_log_id then
        cache:set(last_insert_id_key, 1)
        new_id = cache:get(last_insert_id_key)
    end

    -- debug("------------------["..server_name.."]STORE New ID:" ..tostring(new_id).."----------------------")
    local request_time = get_request_time()
    local referer = ngx_var.http_referer

    local protocol = ngx_var.server_protocol
    local time_key = get_store_key()
    local real_server_name = server_name
    if server_name == no_binding_server_name then
        real_server_name = ngx_var.server_name
    end

    local logline = {
        id = new_id,
        time_key = time_key,
        time = os.time(),
        ip = ip,
        domain = domain,
        server_name = server_name,
        real_server_name = real_server_name,
        method = method,
        status_code = status_code,
        uri = uri,
        request_uri = request_uri,
        body_length = body_length,
        referer = referer,
        user_agent = request_header['user-agent'],
        protocol = protocol,
        is_spider = 0,
        request_time = request_time,
        excluded = excluded,
        request_headers = "",
        ip_list = ip_list,
        client_port = client_port
    }

    local uri_count_request_dict = {
        uri_count_pv = 0,
        uri_count_uv = 0,
        uri_count_ip = 0,
        uri_count_spider_type = nil,
        uri_count_ip_t = nil,
    }

    local request_stat_fields = "req=req+1,length=length+" .. body_length
    local spider_stat_fields = "x"
    local client_stat_fields = "x"
    local uri_client_type_list = {}
    -- debug("Exclude:"..tostring(excluded).."/"..ngx.var.uri)
    if not excluded then

        if status_code == 500 or (method == "POST" and config["record_post_args"] == true) or (status_code == 403 and config["record_get_403_args"] == true) then
            local data = ""
            local ok, err = pcall(function()
                data = get_http_original()
            end)
            if ok and not err then
                logline["request_headers"] = data
            end
            -- debug("Get http orgininal ok:"..tostring(ok))
            -- debug("Get http orgininal res:"..tostring(data))
            -- cache_value(new_id, "request_headers", ngx.req.raw_header())
        end

        -- if ngx_re_find("500,501,502,503,504,505,506,507,509,510,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,421,422,423,424,425,426,449,451", tostring(status_code), "jo") then
        if error_codes[status_code] then
            local field = "status_" .. status_code
            request_stat_fields = request_stat_fields .. "," .. field .. "=" .. field .. "+1"
        end
        -- debug("method:"..method)
        local lower_method = string_lower(method)
        -- if ngx_re_find("get,post,put,patch,delete", lower_method, "ijo") then
        if http_methods[lower_method] then
            local field = "http_" .. lower_method
            request_stat_fields = request_stat_fields .. "," .. field .. "=" .. field .. "+1"
        end
        local ipc = 0
        local pvc = 0
        local uvc = 0
        local uri_uvc = 0
        local uri_ipc = 0
        local is_spider = false
        local request_spider = nil
        local spider_index = 0
        -- local spider_cache_key = spider_cache_prefix..spider_version.."_"..ip
        local spider_cache_key = spider_cache_prefix .. "_" .. ip
        local spider_cache = cache:get(spider_cache_key)
        if spider_cache then
            -- debug("get match result from cache:"..spider_cache)
            local t = split_bylog(spider_cache, ",")
            if t[1] == "false" then
                is_spider = false
            else
                is_spider = true
            end
            if t[2] == "nil" then
                request_spider = nil
            else
                request_spider = t[2]
            end
            spider_index = tonumber(t[3])
        else
            -- 先匹配IP
            is_spider, request_spider, spider_index = match_spider_by_ip(ip)
            if not is_spider then
                is_spider, request_spider, spider_index = match_spider(ip)
            else
                local cache_val = tostring(is_spider) .. "," .. tostring(request_spider) .. "," .. tostring(spider_index)
                cache:set(spider_cache_key, cache_val, SEVEN_DAY_TIMEOUT)
            end
        end
        -- debug("Is spider:"..tostring(is_spider==true))
        -- debug("Request spider:".. tostring(request_spider))
        -- debug("Spider index:".. tostring(spider_index))
        if not is_spider then
            local ua = ''
            if request_header['user-agent'] then
                ua = request_header['user-agent']
            end
            if not ua then
                client_stat_fields = ""
            else
                local client_cache_key = client_cache_prefix .. server_name .. "_" .. ua
                local uri_client_cache_key = client_cache_prefix .. server_name .. "_uri_client_count" .. ua
                local client_cache_val = cache:get(client_cache_key)
                local uri_client_cache_val = cache:get(uri_client_cache_key)
                --debug("uri_client_cache_val: --> " .. uri_client_cache_val)

                if client_cache_val and uri_client_cache_val then
                    -- debug("get client stat result from cache:"..client_cache_val)
                    client_stat_fields = client_cache_val
                    uri_client_type_list = json.decode(uri_client_cache_val)
                else
                    client_stat_fields, uri_client_type_list = match_client(ua)
                    cache:set(uri_client_cache_key, json.encode(uri_client_type_list), client_cache_timeout)
                    cache:set(client_cache_key, client_stat_fields, client_cache_timeout)
                end
            end

            -- debug("Client stat fields:"..tostring(client_stat_fields))
            if not client_stat_fields or #client_stat_fields == 0 then
                client_stat_fields = request_stat_fields .. ",other=other+1"
            end

            if string_find(client_stat_fields, "machine") then
                if statistics_machine_access then
                    pvc, uvc, uri_uvc = statistics_request()
                end
                -- debug("no statistics.")
            else
                pvc, uvc, uri_uvc = statistics_request()
            end
            ipc, uri_ipc = statistics_ipc()
        else
            -- 假蜘蛛请求统计到request_stat/fake_spider字段
            logline["is_spider"] = spider_index
            local field = "spider"
            if spider_index ~= fake_spider then
                uri_count_request_dict["uri_count_spider_type"] = request_spider
                spider_stat_fields = request_spider .. "=" .. request_spider .. "+" .. 1
            else
                field = "fake_spider"
            end
            request_stat_fields = request_stat_fields .. "," .. field .. "=" .. field .. "+" .. 1
        end

        if ipc > 0 then
            request_stat_fields = request_stat_fields .. ",ip=ip+1"
        end
        if uri_ipc > 0 then
            uri_count_request_dict["uri_count_ip"] = 1
            uri_count_request_dict["uri_count_ip_t"] = ip
        end
        if uri_uvc > 0 then
            uri_count_request_dict["uri_count_uv"] = 1
        end
        if uvc > 0 then
            request_stat_fields = request_stat_fields .. ",uv=uv+1"
        end
        if pvc > 0 then
            uri_count_request_dict["uri_count_pv"] = 1
            request_stat_fields = request_stat_fields .. ",pv=pv+1"
        end
    end

    local stat_fields = request_stat_fields .. ";" .. client_stat_fields .. ";" .. spider_stat_fields
    cache_value(new_id, "STAT_FIELDS", stat_fields)
    cache_value(new_id, "logline", json.encode(logline))
    cache_value(new_id, "uri_count_request_dict", json.encode(uri_count_request_dict))
    cache_value(new_id, "uri_client_type_list", json.encode(uri_client_type_list))
    -- 标记有数据写入
    cache:set(cache_check_key_prefix .. server_name, true, 0)
    -- ngx.log(ngx.ERR, "cached.")
end

function _M.run_logs()
	status_code = ngx.status
	uri = ngx_var.uri
	server_port = ngx_var.server_port
	if uri == '/favicon.ico' or status_code == 0 or status_code == 444 then return true end
	local c_name = ngx_var.server_name
	-- debug("Ngx server name:"..c_name)
	server_name = get_server_name(c_name)
	-- debug("server name:"..server_name)
	if server_name == 'default' or server_name == '_' or server_name == 'phpinfo' then return true end

	config = get_config(server_name)
	if config == nil then return true end

	monitor = config["monitor"]
	if monitor == false then
		-- debug("------------------------站点:"..server_name.."关闭监控----------------------")
		return true
	end
	max_log_id = 99999999999999
	body_length = get_length()


	-- 本机的/flush_data.html请求由插件前端发起，用于刷新缓存数据实时显示数据。
	-- 刷新数据请求不被记录到缓存和统计数据
	local client_ip = ngx_var.remote_addr
	if uri == "/bt_total_flush_data" and client_ip == "127.0.0.1" then
		local args, err = ngx_req.get_uri_args()
		local site = args["server_name"]
		if #site > 128 then
			return false
		end
		site = get_server_name(site)
		if site == no_binding_server_name then
			-- debug("非法站点名。")
			return false
		end
		if site then
			-- debug("Flush site data:"..site)
			cache:set(site.."_FLUSH_DATA", true, 1)
			store_logs(site)
		end
		return true
	end

	if server_name == "127.0.0.1" then
		return true
	end
	
	total_flow()
	total_req_sec()

	cache_logs()
end

local function _store_data()
	local site_name 
	for site_name,_ in pairs(domains)
	do
		data_key = cache_check_key_prefix..site_name
		if cache:get(data_key) then
			cache:delete(data_key)
			-- ngx.log(ngx.ERR, "--Storing "..site_name)
			store_logs(site_name)
			-- ngx.log(ngx.ERR, "--Stored "..site_name)
		end
	end
	if not is_exiting() then
		timer_at(store_interval, _store_data)
	end
end

local function reload_spider_ips()
	-- 重载蜘蛛IP库
	if cache:get(latest_reload_ips) then
		-- debug("最近5分钟重载过，跳过。")
		return
	end

	local reload_key = "RELOAD_SPIDERS"
	if cache:get(reload_key) then 
		-- debug("正在重载中,跳过")
		return 
	end
	cache:set(reload_key, True, 60)
	-- debug("开始重载IP库...")
	spider_names = {
		["1"] = "baidu",
		["2"] = "google",
		["3"] = "qh360",
		["4"] = "sogou",
		["5"] = "yahoo",
		["6"] = "bing",
		["7"] = "bytes"
	}
	local inx = 1
	local spider_name = nil
	repeat
		spider_file_name = tostring(inx)
		spider_name = spider_names[spider_file_name]
		inx = inx + 1
		-- 重新设置蜘蛛IP缓存
		local data = nil 

		if spider_name then
			data = get_spider_json(spider_file_name, false)
		end
		if data then
			local ok,zhizhu_list_data = pcall(function()
				return json.decode(data)
			end)
			if ok then
				for _,k in ipairs(zhizhu_list_data)
				do
					cache:set(ip_spider_prefix..k,spider_name,SEVEN_DAY_TIMEOUT)
				end
				local spiders_key = "SPIDERS_"..spider_file_name
				cache:set(spiders_key,'1',SEVEN_DAY_TIMEOUT)
			end
		end
	until not spider_name

	cache:delete(reload_key)
	cache:set(latest_reload_ips, true, 300)
	-- debug("重载IP库完成。")
end

function _M.init()
	local expend_path = "/usr/local/share/lua/5.1/"
	if not package.path:find(expend_path) then
		package.path = expend_path .. "?.lua;" .. package.path
	end
	if not package.cpath:find(cpath) then
		package.cpath = cpath .. "?.so;" .. package.cpath
	end

	local presult, err = pcall(
		function() 
			json = require "cjson" 
			sqlite3 = require "lsqlite3"
			total_config = require "total_config"
			domains = require "domains"
		end
	)
	if not presult then
		run_error = true
		error_msg = "引入依赖错误："..tostring(err)
		-- debug(error_msg)
		return false
	end

	load_global_exclude_ip()

	global_config = total_config["global"]
	statistics_machine_access = global_config["statistics_machine_access"]

	local_site_config = {}

	reload_spider_ips()

	spider_table = {
		["baidu"] = 1,  -- check
		["bing"] = 2,  -- check 
		["qh360"] = 3, -- check
		["google"] = 4, -- check
		["bytes"] = 5,  -- check
		["sogou"] = 6,  -- check
		["youdao"] = 7,
		["soso"] = 8,
		["dnspod"] = 9,
		["yandex"] = 10,
		["yisou"] = 11,
		["other"] = 12,
		["mpcrawler"] = 13,
		["yahoo"] = 14, -- check
		["duckduckgo"] = 15
	}

	error_codes = {
		[500] = 1, [501] = 1, [502] = 1, [503] = 1, [504] = 1, [505] = 1,
		[506] = 1, [507] = 1, [508] = 1, [509] = 1, [510] = 1, 
		[400] = 1, [401] = 1, [402] = 1, [403] = 1, [404] = 1, [405] = 1, 
		[406] = 1, [407] = 1, [408] = 1, [409] = 1, [410] = 1, [411] = 1, 
		[412] = 1, [413] = 1, [414] = 1, [415] = 1, [416] = 1, [417] = 1,
		[418] = 1, [421] = 1, [422] = 1, [423] = 1, [424] = 1, [425] = 1,
		[426] = 1, [449] = 1, [451] = 1, [499] = 1
	} 

	http_methods = {
		["get"] = 1, ["post"] = 1, ["put"] = 1, ["patch"] = 1, 
		["delete"] = 1
	}

	timer_at(store_interval, _store_data)
	logger_inited = true
	-- debug("total logger inited.")
end

return _M