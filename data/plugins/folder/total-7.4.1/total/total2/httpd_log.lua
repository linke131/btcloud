local version = "1.9"
local cpath = "/www/server/total/"
if not package.cpath:find(cpath) then
    package.cpath = cpath .. "?.so;" .. package.cpath ..";;"
end
if not package.path:find(cpath) then
    package.path = cpath .. "?.lua;" .. package.path
end
local server_name,ip,today,day,body_length,config,method,httpd,cache,tms,cache_count
local hour_str
local cache_count_threshold, cache_interval_threshold = 300, 10
local cjson, sqlite3, memcached, socket
local total_config
local update_day
local data_dir
local no_binding_server_name 
local number_day
local day_column
local flow_column
local spider_column
local day_hour1_column                 = "day_hour1"
local flow_hour1_column                = "flow_hour1"
local spider_hour1_column              = "spider_flow_hour1"
local client_port
local fake_spider                      = 77
local total_db_name                    = "total.db"
local total_db, logs_db
local domains
local ONE_DAY_TIMEOUT                  = 86400
local SEVEN_DAY_TIMEOUT                = 86400
local site_config

local debug_mode = false

local function debug(msg)
    if not debug_mode then return true end
    local fp = io.open('/www/server/total/debug.log', 'ab')
    if fp == nil then
         return nil
    end
    local localtime = os.date("%Y-%m-%d %H:%M:%S")
    if server_name then
        fp:write(server_name.."/"..localtime..":"..tostring(msg) .. "\n")
    else
        fp:write(localtime..":"..tostring(msg) .. "\n")
    end
    fp:flush()
    fp:close()
    return true
end

local function get_config(site)

    local config_data = total_config
    -- local config_data = json.decode(read_file_body_bylog(cpath..'/config.json'))
    local config = nil
    if config_data["global"] == nil then return nil end
    global_config = config_data["global"]
    if key == "monitor" then
        if not global_config["monitor"] then
            return global_config["monitor"]
        end
    end
    if config_data[server_name] == nil then
        config = global_config
    else
        config = config_data[server_name]
        for k, v in pairs(global_config) do
            if config[k] == nil then
                config[k] = v
            end
        end
    end
    return config
end

local function file_exists(file)
    local file = io.open(file, "rb")
    if file then 
        file:close()
        return true 
    end
    return false
end

function check_dir(path)
    local file = io.open(path, "rb")
    if file then file:close() end
    return file ~= nil
end

local function arrlen_bylog(arr)
    if not arr then return 0 end
    count = 0
    for _,v in ipairs(arr)
    do
        count = count + 1
    end
    return count
end

local function split_bylog( str,reps )
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function(w)
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

function get_server_name(c_name)
	if c_name == no_binding_server_name then 
		return no_binding_server_name 
	end
    if c_name == "127.0.0.1" or domains[c_name] then
		return c_name
	end
    local my_name = cache:get(c_name)
    if my_name then return my_name end

    local cache_timeout = 3600
	local simple_domain

	local s,e = string.find(c_name, "[.]")
    if s and e then
	    simple_domain = string.sub(c_name, s+1)
    end

	local determined_name
    local _normal
    for site_name,v in pairs(domains)
    do
        _normal = v["normal"]
        if _normal then
            if _normal[c_name] then
                cache:set(c_name, site_name, cache_timeout)
                return site_name
            end
            if simple_domain and _normal[simple_domain] then
                determined_name = site_name
            end
        end
    end
    if determined_name then
	    cache:set(c_name, determined_name,cache_timeout)
		return determined_name
    end
    local tconf = httpd:activeconfig()
    if not tconf then 
	    cache:set(c_name, no_binding_server_name,cache_timeout)
        return no_binding_server_name 
    end
    local tmp = split_bylog(tconf[1].file,'/')
    if not tmp then 
	    cache:set(c_name, no_binding_server_name,cache_timeout)
        return no_binding_server_name
    end
    local other = string.gsub(tmp[arrlen_bylog(tmp)],'.conf$','')
	cache:set(c_name, other,cache_timeout)
    return other
end

function create_dir(path, create_server_name)
    if httpd:regex(path,"(\\&|\\{|\\}|\\%|\\$|\\+|\\=|\\*|\\@|\\'|\\\"|\\[|\\]|/\\.\\./)",0x01) then
        -- debug("非法路径.")
        return false
    end
    local check_name = get_server_name(create_server_name)
    if check_ame == "httpd-vhosts" then
        return false
    end
    httpd:mkrdir(path)
    return true
end

function write_file_bylog(filename,body,mode)
    local fp = io.open(filename,mode)
    if fp == nil then
        return nil
    end
    fp:write(body)
    fp:flush()
    fp:close()
    return true
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

    -- debug("to load golbal exclude ip.")
	local info_obj = package.loaded["total_config"]
	if info_obj then
		package.loaded["total_config"] = nil
		total_config = require "total_config"
	end

	local global_old_exclude_ip = total_config["global"]["old_exclude_ip"]
	-- debug("global old exclude ip:" ..tostring(global_old_exclude_ip))
	if global_old_exclude_ip then
		-- 加载站点的排除规则
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

	-- set tag
	cache:set(load_key, true)

    -- debug("loaded global exclude ip settings.")
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
    
    -- debug('load exclude over.')

	return true
end

local function exclude_ip(ip)
    if config["exclude_ip"] then
        if config["exclude_ip"][ip] then
            -- debug("Exclude request from ip:"..ip)
            return true
        end
    end
	return false
end

local function get_suffix(uri)
	if not uri then return nil end
	local res = httpd:regex(uri, "[.][^.]+$", 0x01)
	if res then
		return string.sub(res[0], 2)
	end
	return nil
end

local function exclude_extension(uri)
    if not uri then return false end
    local conf = config['exclude_extension']
    if not conf then return false end
    local suffix = get_suffix(uri)
    if not suffix then return false end
    if conf[suffix] then
        -- debug("Exclude suffix:"..suffix)
        return true
    end
    return false
end

local function exclude_url(uri)
    if not uri then return false end
    if not config['exclude_url'] then return false end
    -- local the_uri = string.sub(httpd.unparsed_uri, 2)
    local the_uri = uri
    for _,v in pairs(config['exclude_url'])
    do
        local url = v["url"]
        local mode = v["mode"]
        if mode == "regular" then
            if httpd:regex(the_uri,url,0x01) then
                -- debug("Exclude url("..mode..") by "..url.." Match:"..uri)
                return true
            end
        else
            if the_uri == url then
                -- debug("Exclude url("..mode..") by "..url.." Match:"..uri)
                return true
            end
        end
    end
    return false
end

local function exclude_status(status_code)
    if not config["exclude_status"] then return false end
    local str_status_code = tostring(status_code)
    if config["exclude_status"][str_status_code] then
		-- debug("Exclude reponse status code: "..str_status_code)
        return true
    end
    return false
end

local function is_migrating(store_server_name)
    local file = io.open("/www/server/total/migrating", "rb")
    if file then return true end
	local file = io.open("/www/server/total/logs/"..store_server_name.."/migrating", "rb")
	if file then return true end
	return false
end

function read_file_body_bylog(filename)
    fp = nil
    local ok,err = pcall(function() fp=io.open(filename,'rb') end)
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
    local cdn = config["cdn"]
    if cdn == true then
        for _,v in pairs(config['cdn_headers'])
        do
            if request_header[v] ~= nil and request_header[v] ~= "" then
                client_ip = split_bylog(httpd.headers_in[v],',')[1]
                break;
            end
        end
    end
    if type(client_ip) == 'table' then client_ip = "" end
	if client_ip ~= "unknown" and string.match(client_ip,"^[%w:]+$") then
		return client_ip
	end
    if string.match(client_ip,"^%d+%.%d+%.%d+%.%d+$") == nil or not is_ipaddr_bylog(client_ip) then
        client_ip = httpd.useragent_ip
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

function is_min_bylog(ip1,ip2)
    
    n = 0
    for _,v in ipairs({1,2,3,4})
    do
        if ip1[v] == ip2[v] then
            n = n + 1
        elseif ip1[v] > ip2[v] then
            break
        else
            return false
        end
    end
    return true
end

function is_max_bylog(ip1,ip2)
    n = 0
    for _,v in ipairs({1,2,3,4})
    do
        if ip1[v] == ip2[v] then
            n = n + 1
        elseif ip1[v] < ip2[v] then
            break
        else
            return false
        end
    end
    return true
end

function compare_ip_bylog(ips)
    if ip == 'unknown' then return true end
    if not is_max_bylog(ipn,ips[2]) then return false end
    if not is_min_bylog(ipn,ips[1]) then return false end
    return true
end

function get_length()
    local clen  = httpd.headers_out['Content-Length']
    if clen == nil then clen = 0 end
    if clen == 0 and httpd.filename then
        tmp = httpd:stat(httpd.filename)
          if tmp then clen = tmp.size end
    end
    return tonumber(clen)
end

function get_end_time()
    local s_time = os.time()
    local n_date = os.date("*t",s_time + 86400)
    n_date.hour = 0
    n_date.min = 0
    n_date.sec = 0
    d_time = os.time(n_date)
    return d_time - s_time
end

function get_data_on(filename)
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

-- function save_data_on(filename,data)
-- 	local newdata = json.encode(data)
-- 	local extime = 0;
-- 	if string.find(filename,"%d+-%d+-%d+") then extime = 88400 end
-- 	cache:set(filename,newdata,extime)
-- 	if not cache:get(filename..'_lock') then
-- 		cache:set(filename..'_lock',1,10)
-- 		write_file_bylog(filename,newdata,'wb')
-- 	end
-- end


-- local function get_request_time()
-- 	return -1
-- end

local function get_spiders()
    return require "spiders"
end

function get_spider_json(name)
	-- 读取蜘蛛IP库并缓存
	sfile_name = name
	if cache:get(cpath..sfile_name..'SPIDER') then return cache:get(cpath..sfile_name..'SPIDER') end
    file_path=cpath.."xspiders/"..sfile_name..'.json'
	data = read_file_body_bylog(file_path)
 	if not data then 
		data={}
	end 
	cache:set(cpath..sfile_name..'SPIDER',data,10000)
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
	if cache:get(spiders_key) then 
    	if cache:get(sp_key) then 
        	return true
    	end
    	return false
	end 
	cache:set(spiders_key,'1',86400)
	for _,k in ipairs(zhizhu_list_data)
	do
    	cache:set("SPIDER_"..k,'1',86400)
	end
	if cache:get(sp_key) then 
    	return true
	end
	return false
end

local function match_spider(client_ip)
    -- TODO 加入IP区间判断是否是蜘蛛请求
    -- 匹配蜘蛛请求
    local ua = ''
    if httpd.headers_in['user-agent'] then
        ua = httpd.headers_in['user-agent']
    end
    if not ua then
        return false, nil, 0
    end
    local is_spider = false
    local spider_name = nil
    
    local spider_table = {
        ["baidu"] = 1,
        ["bing"] = 2,
        ["qh360"] = 3,
        ["google"] = 4,
        ["bytes"] = 5,
        ["sogou"] = 6,
        ["youdao"] = 7,
        ["soso"] = 8,
        ["dnspod"] = 9,
        ["yandex"] = 10,
        ["yisou"] = 11,
        ["other"] = 12,
        ["mpcrawler"] = 13,
        ["yahoo"] = 14,
        ["duckduckgo"] = 15
    }

    local res,err = httpd:regex(ua, "(Baiduspider|Bytespider|360Spider|Sogou web spider|Sosospider|Googlebot|bingbot|AdsBot-Google|Google-Adwords|YoudaoBot|Yandex|DNSPod-Monitor|YisouSpider|mpcrawler)", 0x01)
    check_res = true
    if res then
        is_spider = true
        spider_match = string.lower(res[0])
        if string.find(spider_match, "baidu") then
            spider_name = "baidu"
            check_res = check_spider("1", client_ip)
        elseif string.find(spider_match, "bytes") then
            spider_name = "bytes"
            check_res = check_spider("7", client_ip)
        elseif string.find(spider_match, "360") then
            spider_name = "qh360"
            check_res = check_spider("3", client_ip)
        elseif string.find(spider_match, "sogou") then
            spider_name = "sogou"
            check_res = check_spider("4", client_ip)
        elseif string.find(spider_match, "soso") then
            spider_name = "soso"
        elseif string.find(spider_match, "google") then
            spider_name = "google"
            check_res = check_spider("2", client_ip)
        elseif string.find(spider_match, "bingbot") then
            spider_name = "bing"
            check_res = check_spider("6", client_ip)
        elseif string.find(spider_match, "youdao") then
            spider_name = "youdao"
        elseif string.find(spider_match, "dnspod") then
            spider_name = "dnspod"
        elseif string.find(spider_match, "yandex") then
            spider_name = "yandex"
        elseif string.find(spider_match, "yisou") then
            spider_name = "yisou"
        elseif string.find(spider_match, "mpcrawler") then
            spider_name = "mpcrawler"
        end	
    end

    if is_spider then 
        if not check_res then
            return is_spider, spider_name, fake_spider
        end
        return is_spider, spider_name, spider_table[spider_name]
    end
    local other_res, err = httpd:regex(ua, "(Yahoo|Slurp|DuckDuckGo)", 0x01)
    if other_res then
        other_res = string.lower(other_res[0])
        if string.find(other_res, "yahoo") then
            spider_name = "yahoo"
            check_res = check_spider("5", client_ip)
        elseif string.find(other_res, "slurp") then
            spider_name = "yahoo"
        elseif string.find(other_res, "duckduckgo") then
            spider_name = "duckduckgo"
        end
        if not check_res then
            return true, spider_name, fake_spider
        end
        return true, spider_name, spider_table[spider_name]
    end

    return false, nil, 0
end

local function statistics_ipc()
    local ipc = 0 
    local ip_token = server_name..'_'..ip
    if not cache:get(ip_token) then
        ipc = 1
        cache:set(ip_token,1,get_end_time())
    end
    return ipc
end

local function statistics_request()
    -- 计算pv uv
    local pvc = 0
    local uvc = 0
    if method == 'GET' and tonumber(httpd.status) == 200 and body_length > 200 then
        local ua = ''
        if httpd.headers_in['user-agent'] then
            ua = string.lower(httpd.headers_in['user-agent'])
        end

        if httpd.headers_out['content-type'] then
            if string.find(httpd.headers_out['content-type'],'text/html') then
            -- if not httpd:regex(httpd.uri,"[.](js|css|png|jpeg|jpg|gif)$",0x01) then
                -- 判断IP是否重复的时间限定范围是请求的当前时间+24小时
                pvc = 1
                
                if ua then
                    if string.find(ua,'mozilla') then
                        local _today = os.date("%Y-%m-%d")
                        local uv_token = httpd:md5(ip .. httpd.headers_in['user-agent'] .. _today)
                        if not cache:get(uv_token) then
                            uvc = 1
                            cache:set(uv_token,1,get_end_time())
                        end
                    end
                end
            end
        end
    end
    return pvc, uvc
end

local function get_clients()
    -- local clients_json = cpath .. '/config/clients.json'
    -- local clients = get_data_on(clients_json)
    return require "clients"
end

local function match_pc_client(ua, clients)
    local msie = nil
    local msie_pattern = nil
    local safari = nil
    local safari_pattern = nil
    local chrome = nil
    local chrome_pattern = nil
    for column, pattern in pairs(clients) do
        if column == "safari" then
            safari_pattern = pattern
        elseif column == "chrome" then
            chrome_pattern = pattern
        elseif column == "msie" then
            msie_pattern = pattern
        elseif httpd:regex(ua, pattern, 0x01) then
            return column
        end
    end
    if msie_pattern and httpd:regex(ua, msie_pattern, 0x01) then
        return "msie"
    end
    if chrome_pattern and httpd:regex(ua, chrome_pattern, 0x01) then
        return "chrome"
    end
    if safari_pattern and httpd:regex(ua, safari_pattern, 0x01) then
        return "safari"
    end
    return nil
end

local function match_norepeat_client(ua, clients)
    if clients == nil then return end
    for name, pattern in pairs(clients) do
        if httpd:regex(ua, pattern, 0x01) then
            return name
        end
    end
end

local function get_update_field(field, value)
    return field.."="..field.."+"..tostring(value)
end

local function match_client()
    -- 匹配客户端
    local ua = ''
    if request_header['user-agent'] then
        ua = request_header['user-agent']
    end
    if not ua then
        return false, nil
    end
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
    local mobile_res = httpd:regex(ua, mobile_regx, 0x01)
    --mobile
    if mobile_res then
        client_stat_fields = client_stat_fields..","..get_update_field("mobile", 1)
        mobile_res = string.lower(mobile_res[0])
        if mobile_res ~= "mobile" then
            client_stat_fields = client_stat_fields..","..get_update_field(clients_map[mobile_res], 1)
        end
    else
        --pc
        -- 匹配结果的顺序，与ua中关键词的顺序有关
        -- lua的正则不支持|语法
        local pc_regx1 = "(360SE|360EE|360browser|Qihoo|TheWorld|TencentTraveler|Maxthon|Opera|QQBrowser|UCWEB|UBrowser|MetaSr|2345Explorer|Edg[e]*)"
        local pc_res = httpd:regex(ua, pc_regx1, 0x01)
        local cls_pc = nil
        if not pc_res then
            if string.find(ua, "[Ff]irefox") then
                cls_pc = "firefox"
            elseif string.find(ua, "MSIE") or string.find(ua, "Trident") then
                cls_pc = "msie"
            elseif string.find(ua, "[Cc]hrome") then
                cls_pc = "chrome"
            elseif string.find(ua, "[Ss]afari") then
                cls_pc = "safari"
            end
        else
            cls_pc = string.lower(pc_res[0])
        end
        -- debug("UA:"..ua)
        -- debug("Cls pc:"..cls_pc)
        if cls_pc then
            client_stat_fields = client_stat_fields..","..get_update_field(clients_map[cls_pc], 1)
        else
            -- machine and other
            local machine_res, err = httpd:regex(ua, "([Cc]url|HeadlessChrome|[a-zA-Z]+[Bb]ot|[Ww]get|[Ss]pider|[Cc]rawler|[Ss]crapy|zgrab|[Pp]ython|java)", 0x01)
            if machine_res then
                client_stat_fields = client_stat_fields..","..get_update_field("machine", 1)
            else
                -- 移动端+PC端+机器以外 归类到 其他
                client_stat_fields = client_stat_fields..","..get_update_field("other", 1)
            end
        end

        local os_regx = "(Windows|Linux|Macintosh)"
        local os_res = httpd:regex(ua, os_regx, 0x01)
        if os_res then
            os_res = string.lower(os_res[0])
            client_stat_fields = client_stat_fields..","..get_update_field(clients_map[os_res], 1)
        end
    end

    local other_regx = "MicroMessenger"
    local other_res = string.find(ua, other_regx)
    if other_res then
        client_stat_fields = client_stat_fields..","..get_update_field("weixin", 1)
    end
    if client_stat_fields then
        client_stat_fields = string.sub(client_stat_fields, 2)
    end
    return client_stat_fields
end

local function total_flow()
    local flow_key = server_name .. '_flow'
    local flow_write = server_name .. '_flow_write'
    if cache:get(flow_write) then
        cache:incr(flow_key,body_length)
    else
        local write_time = now_timestamp
        local now_flow = cache:get(flow_key)
        if not now_flow then now_flow = 0 end
        now_flow = now_flow + body_length
        local realtime_data = tostring(now_flow)..","..tostring(write_time)
        -- debug("Current realtime data:"..tostring(realtime_data))

        local queue_length = 10
        local position_key = flow_key.."_positon"
        local queue_key = flow_key.."_queue_"

        local req_position = 0
        if cache:get(position_key) == nil then
            cache:set(position_key, 1)
            req_position = 1
        else
            cache:incr(position_key, 1)
            req_position = cache:get(position_key)
            if req_position >= queue_length then
                cache:set(position_key, 1)
                req_position = 1
            end
        end

        cache:set(queue_key..tostring(req_position), realtime_data)

        local data = ""
        for i=1, queue_length, 1 do
            local _d = cache:get(queue_key..tostring(i))
            if _d ~= nil then
                data = data.."\n".._d 
            end
        end

        local path = cpath .. 'logs/' .. server_name
        if not check_dir(path) then 
            local create_res = create_dir(path, server_name) 
            if not create_res then
                return create_res
            end
        end

        local filename = path .. '/flow_sec.json'
        write_file_bylog(filename,tostring(data),'w+')

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
        local write_time = now_timestamp
        local now_ = cache:get(_key)
        if not now_ then now_ = 0 end
        now_ = now_ + 1
        local realtime_data = tostring(now_)..","..tostring(write_time)

        local queue_length = 10
        local position_key = _key.."_positon"
        local queue_key = _key.."_queue_"

        local req_position = 0
        if cache:get(position_key) == nil then
            cache:set(position_key, 1)
            req_position = 1
        else
            cache:incr(position_key, 1)
            req_position = cache:get(position_key)
            if req_position >= queue_length then
                cache:set(position_key, 1)
                req_position = 1
            end
        end

        cache:set(queue_key..tostring(req_position), realtime_data)

        local data = ""
        for i=1, queue_length, 1 do
            local _d = cache:get(queue_key..tostring(i))
            if _d ~= nil then
                data = data.."\n".._d 
            end
        end

        local path = cpath .. 'logs/' .. server_name
        if not check_dir(path) then 
            local create_res = create_dir(path, server_name) 
            if not create_res then
                return create_res
            end
        end
        local filename = path .. '/req_sec.json'
        local write_res = write_file_bylog(filename,data,'w+')

        cache:set(_key,1,2)
        cache:set(_write,1,1)
    end
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


local function is_storing(store_server_name)
    local store_status = cache:get(store_server_name.."_STORING")
    if store_status ~= nil and store_status == true then
        return true 
    end
    return false
end

local function get_store_key()
    return os.date("%Y%m%d%H", os.time())
end

local function update_stat(update_server_name, db, stat_table, key, columns)
    -- 根据指定表名，更新统计数据
    if not columns then return end
    local stmt = db:prepare(string.format("INSERT INTO %s(time) SELECT :time WHERE NOT EXISTS(SELECT time FROM %s WHERE time=:time);", stat_table, stat_table))
    if not stmt then
        return
    end
    stmt:bind_names{time=key}
    stmt:step()
    stmt:finalize()
    local update_sql = "UPDATE ".. stat_table .. " SET " .. columns
    update_sql = update_sql .. " WHERE time=" .. key
    status, errorString = db:exec(update_sql)
end

local function init_logs_db(log_dir, server_name, db_name)
    -- 初始化日志db
    local path = log_dir .."/".. server_name
    if not check_dir(path) then 
        local res = create_dir(path, server_name) 
        if not res then
            return false
        end
    end
    local db_path = path .. "/" .. db_name
    if cache:get(db_path) then
        return
    end
    local db = sqlite3.open(db_path)
    local table_name = "site_logs"
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
        -- debug("初始化日志数据库完成。")
    end
    if db and db:isopen() then
        db:close()
    end
    return true
end


local function init_total_db(log_dir, server_name, db_name)
    -- 初始化日志db
    local path = log_dir .."/".. server_name
    if not check_dir(path) then 
        local res = create_dir(path, server_name) 
        if not res then
            return false
        end
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
        -- 客户端统计明细，按小时统计
        -- 客户端的定义: {client:"Android", column_name:"android"}
        status, errorString = db:exec[[
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
            )
        ]]

        -- 请求分类统计明细，按小时统计
        -- time: 2021032500 时间刻度, 以小时为单位
        status, errorString = db:exec[[
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
                )
        ]]

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
                mpcrawler_flow INTEGER DEFAULT 0, 
                duckduckgo_flow INTEGER DEFAULT 0,
                other_flow INTEGER DEFAULT 0, 
                other INTEGER DEFAULT 0
            )
        ]]
        
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
        -- debug("初始化日志数据库完成。")
    end
    if db and db:isopen() then
        db:close()
    end
    return true
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

local function load_update_hour(update_server_name)
	local _file = cpath.."logs/"..update_server_name.."/update_hour.log"
	local cache_val = cache:get(_file)
	if cache_val then
		return cache_val
	end
	local val = read_file_body_bylog(_file)
	if not val then
		val = hour_str
	end
	cache:set(_file, val, ONE_DAY_TIMEOUT)
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

local function statistics_referer(db, referer, referer_md5, body_length)
	local stat_sql = nil
	stat_sql = "INSERT INTO referer2_stat(referer, referer_md5) SELECT \""..referer.."\",\""..referer_md5.."\" WHERE NOT EXISTS (SELECT referer_md5 FROM referer2_stat WHERE referer_md5=\""..referer_md5.."\");"
	local res, err = db:exec(stat_sql)
	local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..flow_hour1_column.."="..flow_hour1_column.."+"..body_length
	stat_sql = "UPDATE referer2_stat SET "..day_column.."="..day_column.."+1,"..flow_column.."="..flow_column.."+"..body_length..hour_update_sql.." WHERE referer_md5=\""..referer_md5.."\""
	res, err = db:exec(stat_sql)
	return true
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

    if is_spider>0 and is_spider ~= fake_spider then
		local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..spider_hour1_column.."="..spider_hour1_column.."+"..body_length
		stat_sql = "UPDATE uri_stat SET "..day_column.."="..day_column.."+1,"..spider_column.."="..spider_column.."+"..body_length..hour_update_sql.." WHERE uri_md5=\""..uri_md5.."\""
    else
		local hour_update_sql = ","..day_hour1_column.."="..day_hour1_column.."+1,"..flow_hour1_column.."="..flow_hour1_column.."+"..body_length
		stat_sql = "UPDATE uri_stat SET "..day_column.."="..day_column.."+1,"..flow_column.."="..flow_column.."+"..body_length..hour_update_sql.." WHERE uri_md5=\""..uri_md5.."\""
    end
    local res, err = db:exec(stat_sql)
    -- debug("stat uri:"..tostring(uri))
    -- debug("stat uri res:"..tostring(res))
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
    return true
end


-- 存储单行日志
local function store_line(db, stmt, store_server_name, lineno)
    local logvalue = get_value(store_server_name, lineno, "logline")
    if not logvalue then return false end

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
    if not request_uri then
        request_uri = uri
    end
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
        debug("Log stat fields is nil.")
        debug("Logdata:"..logvalue)
    else
        stat_fields = split_bylog(stat_fields, ";")
        request_stat_fields = stat_fields[1]
        client_stat_fields = stat_fields[2]
        spider_stat_fields = stat_fields[3]

        if "x" == client_stat_fields then
            client_stat_fields = nil
        end

        if "x" == spider_stat_fields then
            spider_stat_fields = nil
        end
    end

    -- debug("Request stat fields:"..tostring(request_stat_fields))
    -- debug("Spider stat fields:"..tostring(spider_stat_fields))
    -- debug("Client stat fields:"..tostring(client_stat_fields))

    if not excluded then
        stmt:bind_names{
            time=time,
            ip=ip,
            domain=domain,
            server_name=real_server_name,
            method=method,
            status_code=status_code,
            uri=request_uri,
            body_length=body_length,
            referer=referer,
            user_agent=user_agent,
            protocol=protocol,
            request_time=request_time,
            is_spider=is_spider,
            request_headers=request_headers,
            ip_list=ip_list,
			client_port=client_port
        }
        local res, err = stmt:step()
        if tostring(res) == "5" then
            return false
        end
        stmt:reset()
        update_stat(store_server_name, db, "client_stat", time_key, client_stat_fields)
        update_stat(store_server_name, db, "spider_stat", time_key, spider_stat_fields)
        if referer and string.len(referer) > 0 then
			local in_site_check_res = httpd:regex(referer,"^(http[s]*://)*"..store_server_name,0x01)
            if not in_site_check_res then
                local new_referer
                local s, e = string.find(referer, "?")
                if e ~= nil then
                    if e>0 then
                        e = e - 1
                    else
                        e = 0
                    end
                    new_referer = string.sub(referer, 0, e)
                end
                
                if not new_referer then
                    new_referer = referer
                end
                -- debug("statistics referer: "..referer.."/simple referer:"..new_referer)
                statistics_referer(db, new_referer, httpd:md5(new_referer), body_length)
            end
        end
        local total_uri
        if not request_uri then
            total_uri = uri
        else
            total_uri = request_uri
        end
        if total_uri then
            local new_uri
            local s, e = string.find(total_uri, "?")
            if e ~= nil then
                if e>0 then
                    e = e - 1
                else
                    e = 0
                end
                new_uri = string.sub(total_uri, 0, e)
            end
            
            if not new_uri then
                new_uri = total_uri
            end
            statistics_uri(db, store_server_name, new_uri, httpd:md5(new_uri), body_length, is_spider)
        end
        if ip then
            statistics_ip(db, store_server_name, ip, body_length)
        end
    end
    update_stat(store_server_name, db, "request_stat", time_key, request_stat_fields)
    return true
end

local function store_logs(store_server_name)
    if is_migrating(store_server_name) == true then 
        -- debug("Migrating...")
        return
    end
    local flush_data = false
    local waiting_store_key = store_server_name .. "_WAITING_STORE"
    local flush_data_key = store_server_name .. "_FLUSH_DATA"
    local cache_count_id_key = store_server_name.."_CACHE_COUNT"
    local cache_count = cache:get(cache_count_id_key)
    if not cache_count then cache_count = 0 end
    -- debug("if:"..tostring(cache:get(waiting_store_key) and cache_count < cache_count_threshold))
    if not cache:get(waiting_store_key) or cache_count>cache_count_threshold then
        local x = "go"
    else
        if cache:get(flush_data_key) then
            flush_data = true
        else
            return
        end
    end

    if is_storing(store_server_name) == true then 
        -- debug("其他worker正在存储中，稍候存储。")
        cache:delete(flush_data_key)
        return 
    end

	today = os.date("%Y%m%d")
	day = os.date("%d")
	number_day = tonumber(day)
	day_column = "day"..number_day
	flow_column = "flow"..number_day
	spider_column = "spider_flow"..number_day

	hour_str = os.date("%Y%m%d%H")

    -- debug("Cache count:"..cache_count)
    -- debug("flush data:"..tostring(flush_data))
    local storing_key = store_server_name.."_STORING"
    cache:set(storing_key,true, 60)
    if flush_data == false then
        cache:set(waiting_store_key, os.time(), cache_interval_threshold)
    end
    cache:delete(flush_data_key)

    -- 开始存储数据
    local last_insert_id_key = store_server_name.."_LAST_INSERT_ID"
    local store_start_id_key = store_server_name.."_STORE_START"
    -- 1.计算存储数据区间段
    local last_id = tonumber(cache:get(last_insert_id_key))
    local store_start = tonumber(cache:get(store_start_id_key))
    -- debug("store start:"..tostring(store_start))
    -- debug("flush data:"..tostring(flush_data))
    if store_start == nil then
        store_start = 1
    end
    local store_end = last_id
    if not store_end then
        store_end = 1
    end

    site_config = get_config(store_server_name)
    -- debug("start store.")
    local store_count = 0
    -- local store_start_time = socket.gettime() * 1000
    -- debug("start:"..tostring(store_start).."/end:"..tostring(store_end))
    local stmt2 = nil
    local log_dir = cpath .. 'logs'
	data_dir = site_config["data_dir"]
	if data_dir then
		log_dir = data_dir
	end
	local base_path = log_dir .. '/' .. store_server_name .. "/"

	local total_db_path =  base_path .. total_db_name 

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
    -- debug("open err1:"..tostring(err1))
    -- debug("open err2:"..tostring(err2))
    if logs_db ~= nil then
        stmt2 = logs_db:prepare[[INSERT INTO site_logs(
            time, ip, domain, server_name, method, status_code, uri, body_length,
            referer, user_agent, protocol, request_time, is_spider, request_headers, ip_list)
            VALUES(:time, :ip, :domain, :server_name, :method, :status_code, :uri,
            :body_length, :referer, :user_agent, :protocol, :request_time, :is_spider,
            :request_headers, :ip_list)]]
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
    -- local start_transaction_time = socket.gettime()*1000 
    
	status, errorString = logs_db:exec([[BEGIN TRANSACTION]])
	status, errorString = total_db:exec([[BEGIN TRANSACTION]])
    -- debug("begin transaction.")

	local update_hour = load_update_hour(store_server_name)
	if not update_hour or tostring(update_hour) ~= tostring(hour_str) then
        debug("reset hour data.")
		-- reset
		local update_sql = "UPDATE uri_stat SET "..day_hour1_column.."=0,"..spider_hour1_column.."=0,"..flow_hour1_column.."=0"
		status, errorString = total_db:exec(update_sql)

		update_sql = "UPDATE ip_stat SET "..day_hour1_column.."=0,"..flow_hour1_column.."=0"
		status, errorString = total_db:exec(update_sql)

		update_sql = "UPDATE referer2_stat SET "..day_hour1_column.."=0,"..flow_hour1_column.."=0"
		status, errorString = total_db:exec(update_sql)

		write_update_hour(store_server_name)
	end

    update_day = load_update_day(store_server_name)
    -- debug("update day:"..type(update_day).."/today:"..type(today)..tostring(tostring(update_day)==tostring(today)))
    if not update_day or tostring(update_day) ~= tostring(today) then
        -- reset
        local update_sql = "UPDATE uri_stat SET "..day_column.."=0,"..spider_column.."=0,"..flow_column.."=0"
        status, errorString = total_db:exec(update_sql)

        update_sql = "UPDATE ip_stat SET "..day_column.."=0,"..flow_column.."=0"
        status, errorString = total_db:exec(update_sql)

		update_sql = "UPDATE referer2_stat SET "..day_column.."=0,"..flow_column.."=0"
		status, errorString = total_db:exec(update_sql)
        -- debug("update day status:"..tostring(status))
        -- debug("update day error:"..tostring(errorString))

        write_update_day(store_server_name)
    end

    if store_end >= store_start then
        for i=store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
            end
        end
    else
        local _tmp_store_end = store_end
        store_end = max_log_id
        for i=store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
            end
        end

        store_start = 1
        store_end = _tmp_store_end
        for i=store_start, store_end, 1 do
            if store_line(total_db, stmt2, store_server_name, i) then
                store_count = store_count + 1
                clear_value(store_server_name, i, "logline")
                clear_value(store_server_name, i, "STAT_FIELDS")
            end
        end
    end

    local res, err = stmt2:finalize()
    if tostring(res) ~= "5" then

		local res, err = total_db:execute([[COMMIT]])
		local res, err = logs_db:execute([[COMMIT]])
        -- debug("commited.")

        cache:set(store_start_id_key, store_end)
        cache:decr(cache_count_id_key, store_count)
        local cache_count = cache:get(cache_count_id_key)
        if not cache_count then cache_count = 0 end
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

    -- debug("Stored.")
    cache:set(waiting_store_key, os.time(), cache_interval_threshold)
    cache:set(storing_key, false)
end

local function cache_logs()
    local excluded = false
    ip = get_client_ip_bylog()
    local request_uri = httpd.unparsed_uri
    local uri = httpd.uri
    local status_code = httpd.status
    excluded = exclude_status(status_code) or exclude_extension(uri) or exclude_url(request_uri) or exclude_ip(ip)
    domain = get_domain()
    method = httpd.method
    if method == "" or not method then return apache2.OK end
    if not httpd.notes['RT'] then
        tms = 1
    else
        tms = split_bylog(tostring((httpd:clock() - httpd.notes['RT']) / 1000),'.')[1]
    end
    
    client_port = -1
    local ip_list = httpd.headers_in['x-forwarded-for'] 
    if ip and not ip_list then
        ip_list = ip
    end
    local remote_addr = httpd.useragent_ip
    if not string.find(ip_list, remote_addr) then
        if remote_addr then
            ip_list = ip_list .. "," .. remote_addr
        end
    end
    -- ipn = arrip_bylog(ip)

    local last_insert_id_key = server_name .. "_LAST_INSERT_ID"
    local generating_id_key = server_name .. "GENERATING"
    local cache_count_id_key = server_name .. "_CACHE_COUNT"
    if not cache:get(server_name.."_CLEAR_CACHE_COUNT") then
        cache:delete(server_name.."_CACHE_COUNT")
        cache:set(server_name.."_CLEAR_CACHE_COUNT", true)
        -- debug("Cleared cache count.")
    end
    if not cache:get(cache_count_id_key) then
        cache:set(cache_count_id_key, 1)
    else
        cache:incr(cache_count_id_key, 1)
    end
    
    local new_id = nil
    if not cache:get(last_insert_id_key) then
        cache:set(last_insert_id_key, 1)
        new_id = 1
    else
        new_id = tonumber(cache:incr(last_insert_id_key, 1))
        if new_id >= max_log_id then
            cache:set(last_insert_id_key, 1)
            new_id = 1
        end
    end
    -- debug("Store count2:"..tostring(cache:get(cache_count_id_key)))

    -- debug("New id:"..tostring(new_id))
    local request_time = tms
    local referer = httpd.headers_in['referer'] 

    local protocol = httpd.protocol
    local is_spider = 0
    local time_key = get_store_key()
    local user_agent = httpd.headers_in['user-agent']
    local real_server_name = server_name
    if server_name == no_binding_server_name then
        real_server_name = httpd.server_name
    end
        
    local logline = {
        id=new_id,
        time_key=time_key,
        time=os.time(), 
        ip=ip, 
        domain=domain,
        server_name=server_name, 
        real_server_name=real_server_name,
        method=method, 
        status_code=status_code, 
        uri=uri, 
        request_uri=request_uri,
        body_length=body_length, 
        referer=referer, 
        user_agent=request_header['user-agent'], 
        protocol=protocol,
        is_spider=0,
        request_time=request_time,
        excluded=excluded,
        request_headers="",
        ip_list=ip_list
    }

    local request_stat_fields = "req=req+1,length=length+"..body_length
    local spider_stat_fields = "x"
    local client_stat_fields = "x"
    local is_spider = false
    local request_spider = nil
    local spider_index = 0
    -- debug("Excluded:"..tostring(excluded).."/uri:"..httpd.uri)
    if not excluded then
        -- if status_code == 500 or (method=="POST" and config["record_post_args"]==true) then
        -- 	local data = ""
        -- 	local ok, err = pcall(function() data=get_http_original() end)
        -- 	if ok and not err then
        -- 		logline["request_headers"] = data
        -- 	end
        -- 	debug("Get http orgininal ok:"..tostring(ok))
        -- 	debug("Get http orgininal res:"..tostring(data))
        -- end

        if string.find("500,501,502,503,504,505,506,507,509,510,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,421,422,423,424,425,426,449,451,499", status_code) then
            local field = "status_"..status_code
            request_stat_fields = request_stat_fields .. ","..field.."="..field.."+1"
        end
        local lower_method = string.lower(method)
        if string.find("get,post,put,patch,delete", lower_method) then
            local field = "http_"..lower_method
            request_stat_fields = request_stat_fields .. ","..field.."="..field.."+1"
        end

        local ipc = 0
        local pvc = 0
        local uvc = 0
        is_spider, request_spider, spider_index = match_spider(ip)
        if not is_spider then
            client_stat_fields  = match_client()	
            -- debug("Client stat fields:"..tostring(client_stat_fields))
            if #client_stat_fields == 0 then
                client_stat_fields = request_stat_fields..",other=other+1"
            else
                if string.find(client_stat_fields, "machine") then
                    if statistics_machine_access then
                        pvc, uvc = statistics_request()
                    end	
                else
                    pvc, uvc = statistics_request()
                end
            end
            ipc = statistics_ipc()
        else
            logline["is_spider"] = spider_index
            local field = "spider"
            if spider_index ~= fake_spider then
                spider_stat_fields = request_spider.."="..request_spider.."+"..1
            else
                field = "fake_spider"
            end
            request_stat_fields = request_stat_fields .. ","..field.."="..field.."+"..1
        end
        if ipc > 0 then 
            request_stat_fields = request_stat_fields..",ip=ip+1"
        end
        if uvc > 0 then 
            request_stat_fields = request_stat_fields..",uv=uv+1"
        end
        if pvc > 0 then
            request_stat_fields = request_stat_fields..",pv=pv+1"
        end
        -- debug("Is spider:"..tostring(is_spider))
    end
    cache_value(new_id, "STAT_FIELDS", request_stat_fields..";"..client_stat_fields..";"..spider_stat_fields)
    cache_value(new_id, "logline", json.encode(logline))
    -- debug("Cached.")
end

function set_request_time(r)
    r.notes['RT'] = r:clock()
    return apache2.DECLINED
end

function run_logs(request)
    httpd = request
    if httpd.uri == '/favicon.ico' or httpd.status == 0 or httpd.status == 416 then return apache2.OK end
    local presult, err = pcall(
        function() 
            json = require "cjson" 
            memcached = require "memcached"
            sqlite3 = require "lsqlite3"
            total_config = require "total_config"
        end
    ) 
    
    if not presult then 
        -- debug("引入依赖出现错误:"..tostring(err))
        return apache2.OK
    end

    -- debug("connect to memcached.")
    cache = memcached.Connect("127.0.0.1", 11211)
    if not cache then
        cache = memcached.Connect("localhost", 11211)
    end
    if not cache then return apache2.OK end

    no_binding_server_name = "btunknownbt"
    local c_name = httpd.server_name
    domains = require "domains"
    server_name = string.gsub(get_server_name(c_name),'_','.')
    if server_name == 'phpinfo' then return apache2.OK end
    -- debug("Server name:"..server_name)
    -- debug("uri:"..httpd.uri)

    config = get_config(server_name)
    if config == nil then return true end
    monitor = config["monitor"]
    if monitor == false then
        -- debug("------------------------站点:"..server_name.."关闭监控----------------------")
        return apache2.OK
    end

    max_log_id = 99999999999999

    request_header = httpd.headers_in
    out_header = httpd.headers_out

    -- /bt_total_flush_data 请求由插件前端发起，用于刷新缓存数据实时显示数据。
    -- 刷新数据请求不被记录到缓存和统计数据
    local client_ip = httpd.useragent_ip
    if httpd.uri == "/bt_total_flush_data" and client_ip == "127.0.0.1" then
        -- debug("To flush data.")
        local args, multi_args = httpd:parseargs()
        local site = args["server_name"]
        if #site > 128 then
            return apache2.OK
        end
		site = get_server_name(site)
        -- print("check server name:"..site)
		if site == no_binding_server_name or site == "httpd-vhosts" then
            -- debug("未知站点名称.")
			return false
		end
        if site then
            -- debug("To flush site:"..site)
            cache:set(site.."_FLUSH_DATA", true, 1)  
            store_logs(site)
        end
        return apache2.OK
    end

    if server_name == "httpd-vhosts" or server_name == "127.0.0.1" then
        return apache2.OK
    end

    -- debug("Monitor status:"..tostring(monitor))
    -- error_log()
    
    body_length = get_length()
    now_timestamp = os.time(os.date("*t"), os.time())

    total_flow()
    total_req_sec()

    statistics_machine_access = config["statistics_machine_access"]
    -- debug("Statistics machine access:"..tostring(statistics_machine_access))

    if server_name ~= no_binding_server_name then
        load_global_exclude_ip()
        load_exclude_ip(server_name)
    end
    -- debug("to cache.")
    cache_logs()
    -- debug('to store.')
    store_logs(server_name)
    return apache2.OK
end