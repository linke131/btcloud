require "apache2"
if not string.find(package.path,'/www/server/speed/') then
    package.path = "/www/server/speed/?.lua;" .. package.path
end
local total_path = '/www/server/speed/total'
local conf = require "config"
local gzip  = require "gzip"
local request_header = nil
local client_type = '_pc'
local today = nil
local data_key = nil
local server_name = nil
local login_cookie = 'X_CACHE'
local xkey = 'X_CACHE_KEY'
local resp_headers = nil
local memcached = require "memcached"
local cache,httpd
local buff_data = ""


function get_headers_key(k)
    if k == 'connection' then return 'Connection' end
    if k == 'cache-control' then return 'Cache-Control' end
    if k == 'content-type' then return 'Content-Type' end
    if k == 'date' then return 'Date' end
    if k == 'expires' then return 'Expires' end
    if k == 'link' then return 'Link' end
    if k == 'transfer-encoding' then return 'Transfer-Encoding' end
    if k == 'content-length' then return 'Content-Length' end
    if k == 'server' then return 'Server' end
    if k == 'set-cookie' then return 'Set-Cookie' end
    if k == 'content-encoding' then return 'Content-Encoding' end
    if k == 'vary' then return 'Vary' end
    if k == 'x-content-type-options' then return 'X-Content-Type-Options' end
    if k == 'strict-transport-security' then return 'Strict-Transport-Security' end
    if k == 'x-frame-options' then return 'X-Frame-Options' end
    if k == 'x-xss-protection' then return 'X-Xss-Protection' end
    return k
end

function debug(msg)
    write_file_debug('/www/server/speed/1.log',tostring(msg) .. "\n","ab")
end

--分割字符串
function split(input, delimiter)
    input = tostring(input)
    delimiter = tostring(delimiter)
    if (delimiter=='') then return false end
    local pos,arr = 0, {}
    for st,sp in function() return string.find(input, delimiter, pos, true) end do
        table.insert(arr, string.sub(input, pos, st - 1))
        pos = sp + 1
    end
    table.insert(arr, string.sub(input, pos))
    return arr
end

function httpd_match(s_data,s_find)
    return httpd:regex(s_data,s_find,0x01)
end

--构造规则
function get_rules(rules)
    if rules == nil then return {} end
    if type(rules) == 'string' then
        rules = {rules}
    end
    return rules
end


--检查Cookie
function is_cookie(rules)
    if request_header['Cookie'] == nil then return conf.sites[server_name].empty_cookie end
    rules = get_rules(rules)
    for i,rule in ipairs(rules)
    do
        if httpd_match(request_header['Cookie'],rule) then
            return false
        end
    end
    return true
end

--获取客户端IP
function get_client_ip()
    local client_ip = "unknown"
	for _,v in ipairs(conf.settings.ip_for)
	do
		if request_header[v] ~= nil and request_header[v] ~= "" then
			client_ip = split(request_header[v],',')[1]
			break;
		end
	end

	if type(client_ip) == 'table' then client_ip = "" end
	if string.match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil then
		client_ip = httpd.useragent_ip
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

--IP地址转整数
function ip2long( str )
	local num = 0
	if str and type(str)=="string" then
		local o1,o2,o3,o4 = str:match("(%d+)%.(%d+)%.(%d+)%.(%d+)")
		if o1 == nil or o2 == nil or o3 == nil or o4 == nil then return 0 end
		num = 2^24*o1 + 2^16*o2 + 2^8*o3 + o4
	end
    return num
end

--检查客户IP
function is_client_ip(ips)
    local client_ip = get_client_ip()
    if string.match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil then return true end
    local iplong = ip2long(client_ip)
    for _,ip in ipairs(ips) do
        if iplong >= ip[1] and iplong <= ip[2] then
            return false
        end
    end
    return true
end

--获取server_name
function get_server_name_byspeed()
	local c_name = httpd.server_name
	local my_name = cache:get(c_name)
	if my_name then return my_name end

	if conf.sites[c_name] then return c_name end
	for k,val in pairs(conf.sites) do
		for _,d_name in ipairs(val.domains)
		do
			if c_name == d_name then
				cache:set(c_name,k,3600)
				return k
			end
		end
	end
	local tconf = httpd:activeconfig()
	if not tconf then return c_name end
	local tmp = split(tconf[1].file,'/')
	if not tmp then return c_name end
	return string.gsub(tmp[#tmp],'.conf$','')
end

--获取指定cookie
function get_cookie(key)
    if not request_header['Cookie'] or request_header['Cookie'] == nil then
        return nil
    end
    local cookie_tmp = split(request_header['Cookie'],';')
    for _,nl in ipairs(cookie_tmp) do
        local cookie_key = split(nl,'=')
        if cookie_key[1]:match("^%s*(.-)%s*$") == key then
            return cookie_key[2]
        end
    end
    return nil
end


function is_hit()
    if not conf.sites or not conf.settings then return false end
    if not conf.settings.open then return false end
    if not conf.sites[server_name] then return false end
    if not conf.sites[server_name].open then return false end
    if not is_cookie(conf.sites[server_name].white.cookie) then return false end
    return true
end


function read_file_body(filename)
	local fp = io.open(filename,'r')
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

function write_file(filename,body)
	local fp = io.open(filename,'w+')
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end


function write_file_debug(filename,body,mode)
	local fp = io.open(filename,mode)
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end

--目录是否存在
function check_dir(path)
	local file = io.open(path, "rb")
	if file then file:close() end
	return file ~= nil
end

--创建目录
function create_dir(path)
    httpd:mkrdir(path)
	--os.execute("mkdir -p " .. path)
end

--创建统计目录
function create_total_dir()
    if not server_name then return false end
    local check_key = server_name..'check_dir'
    if cache:get(check_key) then
        return true
    end
    if not check_dir(total_path) then
        create_dir(total_path)
    end

    local s_path = total_path .. '/' .. server_name
    if not check_dir(s_path) then
        create_dir(s_path)
    end

    local s_path = total_path .. '/' .. server_name .. '/request'
    if not check_dir(s_path) then
        create_dir(s_path)
    end

    local s_path = total_path .. '/' .. server_name .. '/hit'
    if not check_dir(s_path) then
        create_dir(s_path)
    end
    cache:set(check_key,1,10)
end

--检查URI
function is_uri_get(rules)
    rules = get_rules(rules)
    for k,v in  ipairs(rules) do
        if httpd_match(httpd.uri,v) then
            return false
        end
    end
    return true
end

--统计请求数
function total_request()
    if #conf.sites[server_name].white.not_uri > 0 then
        if is_uri_get(conf.sites[server_name].white.not_uri) then
            return false
        end
    end

    local key1 = httpd:md5(server_name ..'_request_total')
    local key2 = httpd:md5(server_name ..'_request_site_total')
    local key3 = httpd:md5(server_name ..'_request_site_today'..today)

    local request_total = cache:get(key1)
    local total_file = total_path .. '/total.json'
    if not request_total then
        local tmp_fb = read_file_body(total_file)
        if tmp_fb then
            request_total = tonumber(tmp_fb)
        else
            request_total = 0
        end
    end

    local request_site_total = cache:get(key2)
    local total_site_file = total_path .. '/' .. server_name .. '/total.json'
    if not request_site_total then
        local tmp_fb = read_file_body(total_site_file)
        if tmp_fb then
            request_site_total = tonumber(tmp_fb)
        else
            request_site_total = 0
        end
    end

    local request_site_today = cache:get(key3)
    local total_site_today_file =  total_path .. '/' .. server_name .. '/request/'..today..'.json'
    if not request_site_today then
        local tmp_fb = read_file_body(total_site_today_file)
        if tmp_fb then
            request_site_today = tonumber(tmp_fb)
        else
            request_site_today = 0
        end
    end

    if not request_total then request_total = 0 end
    if not request_site_total then request_site_total = 0 end
    if not request_site_today then request_site_today = 0 end

    request_total = request_total + 1
    request_site_total = request_site_total + 1
    request_site_today = request_site_today + 1
    if cache:get(key1) then
        cache:incr(key1,1)
        cache:incr(key2,1)
        cache:incr(key3,1)
    else
        cache:set(key1,request_total,86400)
        cache:set(key2,request_site_total,86400)
        cache:set(key3,request_site_today,86400)
    end
    local key4 = 'is_req_cache_write'
    if not cache:get(key4) then
        write_file(total_file,tostring(request_total))
        write_file(total_site_file,tostring(request_site_total))
        write_file(total_site_today_file,tostring(request_site_today))
        cache:set(key4,1,2)
    end
end

--统计命中数
function total_hit()
    local key1 = httpd:md5(server_name ..'_hit_total')
    local key2 = httpd:md5(server_name ..'_hit_site_total')
    local key3 = httpd:md5(server_name ..'_hit_site_today'..today)

    local request_total = cache:get(key1)
    local total_file = total_path .. '/hit.json'
    if not request_total then
        local tmp_fb = read_file_body(total_file)
        if tmp_fb then
            request_total = tonumber(tmp_fb)
        else
            request_total = 0
        end
    end

    local request_site_total = cache:get(key2)
    local total_site_file = total_path .. '/' .. server_name .. '/hit.json'
    if not request_site_total then
        local tmp_fb = read_file_body(total_site_file)
        if tmp_fb then
            request_site_total = tonumber(tmp_fb)
        else
            request_site_total = 0
        end
    end

    local request_site_today = cache:get(key3)
    local total_site_today_file =  total_path .. '/' .. server_name .. '/hit/'..today..'.json'
    if not request_site_today then
        local tmp_fb = read_file_body(total_site_today_file)
        if tmp_fb then
            request_site_today = tonumber(tmp_fb)
        else
            request_site_today = 0
        end
    end

    if not request_total then request_total = 0 end
    if not request_site_total then request_site_total = 0 end
    if not request_site_today then request_site_today = 0 end

    request_total = request_total + 1
    request_site_total = request_site_total + 1
    request_site_today = request_site_today + 1
    if cache:get(key1) then
        cache:incr(key1,1)
        cache:incr(key2,1)
        cache:incr(key3,1)
    else
        cache:set(key1,request_total,86400)
        cache:set(key2,request_site_total,86400)
        cache:set(key3,request_site_today,86400)
    end
    local key4 = 'is_hit_cache_write'
    if not cache:get(key4) then
        write_file(total_file,tostring(request_total))
        write_file(total_site_file,tostring(request_site_total))
        write_file(total_site_today_file,tostring(request_site_today))
        cache:set(key4,1,2)
    end
end

function to_hit(req_data)
    set_headers()
    httpd:puts(req_data);
    return apache2.DONE
end

function to_content_type()
    if httpd.headers_out['Content-Type'] == nil or httpd.headers_out['Content-Type'] == 'application/octet-stream' then
        httpd.headers_out['Content-Type'] = "text/html"
    end
end

function to_miss()
    --to_content_type()
    httpd.headers_out['X-Cache'] = 'MISS'
    total_request()
    return apache2.DECLINED
end

function set_headers()
    local sp = "__PANEL__"
    local sp2 = "__BT__"
    local sp3 = "__BAOTA__"
    local h_tmp = cache:get(data_key..'_h');
    header_data = split(h_tmp,sp2)
    for _,v in ipairs(header_data) do
        if v then
            kv = split(v,sp)
            k = get_headers_key(kv[1])
            if kv[2] then
                if string.find(kv[2],sp3) then
                    kv[2] = split(kv[2],sp3)
                end
                if k ~= 'Connection'
                and k ~= 'Transfer-Encoding'
                and k ~= 'Content-Encoding'
                and k ~= 'x-cache'
                and k ~= 'Vary'
                and k ~= 'Strict-Transport-Security'
                and k ~= 'X-Frame-Options'
                and k ~= 'X-Xss-Protection'
                and k ~= 'X-Content-Type-Options'
                and k ~= 'Set-Cookie' then
                    httpd.headers_out[k] = kv[2]
                end
            end
        end
    end
    to_content_type()
    httpd.headers_out['X-Cache'] = 'HIT'
end



function get_cookie_tips()
    local x_last = tostring(httpd:clock())
    local x_tip = httpd:md5(x_last)
    return x_tip
end

function is_level()
    if conf.settings == nil then return false end
    if conf.settings['level'] == nil or conf.settings['level'] == 0 then return true end

    local hit_today_file = total_path .. '/' .. server_name .. '/hit/'..today..'.json'
    local today_hit = read_file_body(hit_today_file)
    if not today_hit then
        today_hit = 0
    end
    today_hit = tonumber(today_hit)
    if conf.settings['level'] == 1 then
        if today_hit > 0xc3500 then return false end
    else
        if today_hit > 0xc350 then return false end
    end
    return true
end



function mod_exists(name)
    if package.loaded[name] then
        return true
    else
        for _,searcher in ipairs(package.searchers or package.loaders) do
            local loader = searcher(name)
            if type(loader) == 'function' then
                package.preload[name] = loader
                return true
            end
        end
        return false
    end
end


--获取响应头
function get_headers()
	local resp_headers_table = {}
	local hes = {"Connection","Cache-Control","Content-Type","Date","Expires","Content-Length","Server","Set-Cookie","Content-Encoding","Vary"}
    for i,v in ipairs(hes) do
		local h_tmp = resp_headers[v]
		if h_tmp == nil then
			h_tmp = resp_headers[string.lower(v)]
		end
		if h_tmp then
			resp_headers_table[v] = h_tmp
		end
	end

    local s_headers = ""
    local sp = "__PANEL__"
    local sp2 = "__BT__"
    local sp3 = "__BAOTA__"
    for k,v in pairs(resp_headers_table) do
        if type(v) == 'string' then
            --if k ~= 'set-cookie' or k ~= 'Set-Cookie' then
            s_headers = s_headers .. k .. sp .. v .. sp2
            --end
        else
            local kv_tmp = ''
            local sl = #v
            for i,val in ipairs(v) do
                if i < sl then
                    kv_tmp = kv_tmp .. val .. sp3
                else
                    kv_tmp = kv_tmp .. val
                end
            end
            s_headers = s_headers .. k .. sp .. kv_tmp .. sp2
        end
    end
    return s_headers
end


--检查请求类型
function is_method(rules)
    rules = get_rules(rules)

    local method = httpd.method

    for i,rule in ipairs(rules) do
        if method == rule then
            return false
        end
    end
    return true
end

--检查响应头
function is_resp_headers(key,rules)
    rules = get_rules(rules)
    header_value = httpd.headers_out[key]
    for i,rule in ipairs(rules) do
        if header_value == rule then
            return false
        end
    end
    return true
end

--检查请求头
function is_req_headers(rules)
    if request_header == nil or rules == nil then return true end
    rules = get_rules(rules)

    for k,v in pairs(request_header) do
        for key,val in pairs(rules) do
            if k == key then
                if not val then return false end
                if httpd_match(request_header[k] , val) then
                    return false
                end
            end
        end
    end
    return true
end

--检查URI
function is_uri(rules)
    rules = get_rules(rules)
    for k,v in  ipairs(rules) do
        if httpd_match(uri,v) then
            return false
        end
    end
    return true
end

--检查扩展名
function is_ext(rules)
    rules = get_rules(rules)
    for k,v in  ipairs(rules) do
        if httpd_match(uri,'.'.. v .. '$') then
            return false
        end
    end
    return true
end

--检查响应类型
function is_type(rules)
    rules = get_rules(rules)
    if content_type == nil then return false end
    for k,v in  ipairs(rules) do
        if httpd_match(content_type,v) then
            return false
        end
    end
    return true
end

--检查响应状态
function is_status(rules)
    rules = get_rules(rules)
    for k,v in  ipairs(rules) do
        if httpd.status == v then
            return false
        end
    end
    return true
end

--检查host
function is_host(rules)
    rules = get_rules(rules)
    for k,v in  ipairs(rules) do
        if httpd.hostname == v then
            return false
        end
    end
    return true
end

--检查请求参数
function is_args(rules)
    rules = get_rules(rules)
    for k,v in pairs(uri_request_args) do
        for _,rule in ipairs(rules) do
            if k == rule then
                return false
            end
        end
    end
    return true
end

--检查白名单
function is_white()
    if not conf.sites[server_name].white then return false end
    if #conf.sites[server_name].white.not_uri > 0 then
        if is_uri(conf.sites[server_name].white.not_uri) then
            return true
        end
    end
    if not is_cookie(conf.sites[server_name].white.cookie) then return true end
    if not is_method(conf.sites[server_name].white.method) then return true end
    if not is_uri(conf.sites[server_name].white.uri) then return true end
    if not is_host(conf.sites[server_name].white.host) then return true end
    if not is_client_ip(conf.sites[server_name].white.ip) then return true end

    if not is_ext(conf.sites[server_name].white.ext) then return true end
    if not is_type(conf.sites[server_name].white.type) then return true end
    return false
end

--检查是否强制缓存
function is_force()
    if not conf.sites[server_name].force then return false end
    if not is_uri(conf.sites[server_name].force.uri) then return true end
    if not is_host(conf.sites[server_name].force.host) then return true end
    if not is_client_ip(conf.sites[server_name].force.ip) then return true end
    if not is_ext(conf.sites[server_name].force.ext) then return true end
    if not is_type(conf.sites[server_name].force.type) then return true end
    return false
end

--检查响应头是否包含no-cache标记
function is_no_cache()
    if not resp_headers then return false end
    cache_control = resp_headers['cache-control']
    if not cache_control then
        cache_control = resp_headers['Cache-Control']
    end
    if not cache_control then return false end
    if cache_control == 'no-cache' then return true end
    if type(cache_control) == 'table' then
        if string.find(cache_control[1],'no%-cache') then return true end
    else
        if string.find(cache_control,'no%-cache') then return true end
    end
    return false
end


--检查是否缓存
function is_cache()
    if httpd.headers_out['X-Cache'] == 'HIT' then return false end
    if is_force() then return true end
    if conf.sites[server_name]['is_no_cache'] == nil then
        if is_no_cache() then return false end
    end
    if is_white() then return false end
    return true
end


function get_uri()
    tmp = split(httpd.the_request,' ')
    if #tmp < 3 then return httpd.the_request end
    return tmp[2]
end


--设置登录标记
function set_login_tips(sessionid)
    cache:set(sessionid,1,86400 * 7)
    if cache:get(sessionid .. 'miss') then
        cache:delete(sessionid .. 'miss')
    end
end


--登录检测
function login_check()
    if conf.sites[server_name]['login_success'] == nil then
        return false
    end
    if conf.sites[server_name]['login_success']['sessionid_key'] == '' or conf.sites[server_name]['login_success']['sessionid_key'] == nil then
        return false
    end
    if conf.sites[server_name]['login_success']['method'] ~= 'ALL' then
        if httpd.method ~= conf.sites[server_name]['login_success']['method'] then
            return false
        end
    end

    local sessionid = get_cookie(xkey)
    if sessionid == nil then
        return false
    end


    local is_succ = false
    if type(conf.sites[server_name]['login_success']['uri']) == 'table' then
        for _,login_uri in ipairs(conf.sites[server_name]['login_success']['uri']) do
            if httpd_match(uri,login_uri) then
                is_succ = true
            end
        end
    end

    if not is_succ then  return false end
    if type(conf.sites[server_name]['login_success']['success']) ~= 'table' then
        if httpd.status == conf.sites[server_name]['login_success']['success'] then
            set_login_tips(sessionid)
            return true
        else
            return false
        end
    end

    if buff_data then
        local is_login_tips = false
        for _,rule in ipairs(conf.sites[server_name]['login_success']['success']) do
            if type(rule) ~= 'string' then
                if httpd.status == rule then
                    is_login_tips = true
                end
            else
                if httpd_match(buff_data,rule) then
                    is_login_tips = true
                end
            end

            if is_login_tips then
                set_login_tips(sessionid)
                return true
            end
        end
    end
    return false
end

--退出检测
function loginout_check()
    if conf.sites[server_name]['login_out'] == nil then
        return false
    end
    local is_succ = false
    if type(conf.sites[server_name]['login_out']['uri']) == 'table' then
        for _,login_uri in ipairs(conf.sites[server_name]['login_out']['uri']) do
            if httpd_match(uri,login_uri) then
                is_succ = true
            end
        end
    end

    if not is_succ then return false end
    if conf.sites[server_name]['login_out']['method'] ~= 'ALL' then
        if httpd.method ~= conf.sites[server_name]['login_out']['method'] then
            return false
        end
    end

    local sessionid = get_cookie(xkey) --get_cookie(conf.sites[server_name]['login_success']['sessionid_key'])

    if sessionid == nil then
        return false
    end
    if not cache:get(sessionid) then
        return false
    end
    if type(conf.sites[server_name]['login_out']['success']) == 'table' then
        if buff_data then
            for _,rule in ipairs(conf.sites[server_name]['login_out']['success']) do
                if type(rule) ~= "string" then
                    if httpd.status == rule then
                        cache:delete(sessionid)
                        cache:set(sessionid .. '_miss',1,10)
                        return true
                    end
                else
                    if httpd_match(buff_data,rule) then
                        cache:delete(sessionid)
                        cache:set(sessionid .. '_miss',1,10)
                        return true
                    end
                end
            end
        end
    end
    return false
end

function init_public()
    request_header = httpd.headers_in
    if request_header['User-Agent'] then
        if httpd:regex(request_header['User-Agent'],"(iPhone|Mobile|Android|iPod|iOS)",0x01) then
            client_type = '_mobile'
        end
    end
    data_key = httpd:md5(httpd.hostname .. ':' .. tostring(httpd.port) .. uri .. client_type)
    server_name = get_server_name_byspeed()
end


function init_get_cache()
    init_public()
    today = os.date("%Y-%m-%d")
end

function init_set_cache()
    init_public()
    resp_headers = httpd.headers_out
end


function get_cache(r)

    if conf.sites == nil then return apache2.DECLINED end
    httpd = r
    if httpd.method ~= 'GET' then return apache2.DECLINED end
    if httpd.hostname == nil then return apache2.DECLINED end

    cache = memcached.Connect("127.0.0.1", 11211)
	if not cache then
		cache = memcached.Connect("localhost", 11211)
	end
	if not cache then return apache2.DECLINED end
    uri = get_uri()
    init_get_cache()

    if conf.sites[server_name] == nil then return apache2.DECLINED end
    if httpd_match(httpd.uri,"^/.*.(jpg|jpeg|png|gif|css|js|woff|ico|gz|mp4|avi|mp3|log|webm|font|woff2|zip|rar|7z|apk|exe|msi)$") then
        return apache2.DECLINED
    end

    if not is_level() then return apache2.DECLINED end
    if is_white() then return apache2.DECLINED end
    create_total_dir()

    --登录检测
    local is_login_cookie = get_cookie(login_cookie)
    if conf.sites[server_name]['login_success'] ~= nil then
        local sessionid = nil
        local x_tip = nil
        if conf.sites[server_name]['login_success']['sessionid_key'] then
            sessionid = get_cookie(xkey)
            if sessionid == nil then
                x_tip = get_cookie_tips()
                httpd:setcookie{
                    key = xkey,
                    value = x_tip,
                    expires = os.time() + 86400,
                    path = '/'
                }
            end
        end
        if x_tip == nil then
            if sessionid == nil then
                sessionid = get_cookie(conf.sites[server_name]['login_success']['sessionid_key'])
            end
        else
            sessionid = x_tip
        end

        if sessionid ~= nil then
	        local login_tip = cache:get(sessionid)
	        local is_miss_cache = cache:get(sessionid .. '_miss')
    	    if login_tip ~= nil then
    	        --如果缓存标记有效，且cookie标记无效，则修改cookie标记为已登录
    	        if is_login_cookie ~= '1' then
                    httpd:setcookie{
                        key = login_cookie,
                        value = "1",
                        expires = os.time() + 86400,
                        path = '/'
                    }
                end
                httpd.headers_out['login-miss'] = '1'
                return to_miss()
            else
                if is_miss_cache then
                    --如果缓存中miss标记有效，则修改cookie标记为未登录
                    if is_login_cookie == '1' then
                        httpd:setcookie{
                            key = login_cookie,
                            value = "0",
                            expires = os.time() + 86400,
                            path = '/'
                        }
                    end
                    httpd.headers_out['login-miss'] = '1'
                    return to_miss()
                else
                    --如果cookie标记有效
                    if is_login_cookie == '1' then
                        cache:set(sessionid,1,86400)
                    end
                end
    	    end
    	end
    end
    if is_login_cookie == '1' then
        httpd.headers_out['login-miss'] = '1'
        return to_miss()
    end


    local req_data = cache:get(data_key)
    if req_data ~= nil then
        if is_hit() then
            total_hit()
            set_headers()
            if request_header['Accept-Encoding'] then
                httpd.headers_out['Vary'] = 'Accept-Encoding'
                httpd:write(req_data)
            else
                local m = gzip.decompress(req_data)
                httpd.headers_out['Content-Length'] = tostring(#m)

                httpd.headers_out['Content-Encoding'] = nil
                httpd:write(m)
            end
            return apache2.DONE
        else
          return to_miss()
        end
    else
        return to_miss()
    end
end



--设置缓存
function Output_filter(r)

    cache = memcached.Connect("127.0.0.1", 11211)
	if not cache then
		cache = memcached.Connect("localhost", 11211)
	end
	if not cache then return apache2.DECLINED end

    httpd = r
    if httpd.hostname == nil then return apache2.DECLINED end
    request_header = httpd.headers_in
    client_type = '_pc'
    if request_header['User-Agent'] then
        if httpd:regex(request_header['User-Agent'],"(iPhone|Mobile|Android|iPod|iOS)",0x01) then
            client_type = '_mobile'
        end
    end

    uri = get_uri()

    data_key = httpd:md5(httpd.hostname .. ':' .. tostring(httpd.port) .. uri .. client_type)
    server_name = get_server_name_byspeed()
    resp_headers = httpd.headers_out
    resp_headers['Content-Type'] = r.content_type
    if not conf.sites or not conf.settings then return apache2.DECLINED end
    if not conf.settings.open then return apache2.DECLINED end


    if not conf.sites[server_name] then return apache2.DECLINED end
    if not conf.sites[server_name].open then return apache2.DECLINED end


    --uri_request_args = httpd:arseargs()
    content_type = r.content_type

    local is_max_len = false
    local max_len = 1024 * 1024
    coroutine.yield()
    while bucket do
        if not is_max_len then
            if not buff_data then
                buff_data = bucket
            else
                buff_data = buff_data .. bucket
            end

            if #buff_data > max_len then
                is_max_len = true
            end
        end
        coroutine.yield(bucket)
    end

    if is_max_len then return apache2.DECLINED end
    if login_check() then return apache2.DECLINED end
	if loginout_check() then return apache2.DECLINED end
	if httpd.status ~= 200 then return apache2.DECLINED end
	if not string.find(content_type,'html') then return apache2.DECLINED end
    if not is_cache() then return apache2.DECLINED end

    if httpd.headers_in['login-miss'] == '1' then
        return apache2.DECLINED
    end

    local is_login_cookie = get_cookie(login_cookie)
    if is_login_cookie == '1' then
        return apache2.DECLINED
    end

    if buff_data then
        resp_headers['Content-Encoding'] = 'gzip'
        s,e = string.byte(buff_data,1,2)
        if s ~= 31 or e ~= 139 then
            buff_data = gzip.compress(buff_data)
        end
        resp_headers['Content-Length'] = tostring(#buff_data)
        local head_data = get_headers()
        cache:set(data_key..'_h',head_data,conf.sites[server_name].expire)
        cache:set(data_key,buff_data,conf.sites[server_name].expire)
    end
    return apache2.DECLINED
end
