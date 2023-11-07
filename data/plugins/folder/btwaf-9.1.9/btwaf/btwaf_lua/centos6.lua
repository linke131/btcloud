--[[
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 梁凯强 <1249648969@qq.com>
# 宝塔Nginx防火墙
# OUT_Time: 2021-04-10
# 祝福大家 2021年一直开心一直快乐,在新的一年中更加美好！！！！  

  ┏┛ ┻━━━━━┛  ┻┓
  ┃　　　━　　 ┃
  ┃　┳┛　  ┗┳  ┃
  ┃　　　-　　 ┃
  ┗━┓　　　┏━━━┛   佛祖保佑、没有bug
    ┃　　　┗━━━━━━━━┓
    ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
      ┗━┻━┛   ┗━┻━┛
]]--
local cpath = "/www/server/btwaf/"
local cpath2 = "/dev/shm/"
local jpath = cpath .. "rule/"
local json = require "cjson"
local cmspath = cpath .. "cms/"
local ngx_match = ngx.re.find
local resolver = require "dns"
local libinjection = require "libinjection"
local multipart = require "multipart"
local error_rule = nil
local is_type =nil


function read_file(name)
    fbody = read_file_body(jpath .. name .. '.json')
    if fbody == nil then
        return {}
    end
    return json.decode(fbody)
end

function get_nginx_cpu()
	return tonumber(read_file_body("/dev/shm/nginx.txt"))
end

function read_file_body(filename)
	fp = io.open(filename,'r')
	if fp == nil then
        return nil
    end
	fbody = fp:read("*a")
    fp:close()
    if fbody == '' then
        return nil
    end
	return fbody
end

function re_png(filename)
	fp = io.open(filename,'rb')
	if fp == nil then
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
	fp = io.open(filename,'w')
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end

local config = json.decode(read_file_body(cpath .. 'config.json'))
local site_config = json.decode(read_file_body(cpath .. 'site.json'))

function is_ipaddr(client_ip)
	if string.find(client_ip,':') then return true end
	local cipn = split(client_ip,'.')
	if arrlen(cipn) < 4 then return false end
	for _,v in ipairs({1,2,3,4})
	do
		local ipv = tonumber(cipn[v])
		if ipv == nil then return false end
		if ipv > 255 or ipv < 0 then return false end
	end
	return true
end

function compare_ip_block(ips)
	if (string.match(ips,"^%d+%.%d+%.%d+%.%d+$") == nil and string.match(ips,"^[%w:]+$") == nil) or ips == 'unknown'  then return false end
	if not ips then return false end
	if ips=='unknown' then return false end 
	if string.find(ips,':') then return false end
	ips = arrip(ips)
	if not is_max(ips,arrip("127.0.0.255")) then return false end
	if not is_min(ips,arrip("127.0.0.1")) then return false end
	return true
end

function get_client_ip_bylog()
	local client_ip = "unknown"
	if site_config[server_name] then
		if site_config[server_name]['cdn'] then
			for _,v in ipairs(site_config[server_name]['cdn_header'])
			do
				if request_header[v] ~= nil and request_header[v] ~= "" then
					local header_tmp = request_header[v]
					if type(header_tmp) == "table" then header_tmp = header_tmp[1] end
					tmpe=split_bylog(header_tmp,',')
                    if arrlen(tmpe)>=1 then 
                        if site_config[server_name]['cdn_baidu'] ~=nil and site_config[server_name]['cdn_baidu'] then 
                            client_ip=tmpe[1]
    				        client_ip=string.gsub(client_ip," ","")
                        else
    				        client_ip=tmpe[arrlen(tmpe)]
    				        client_ip=string.gsub(client_ip," ","")
				        end 
						if request_header['remote-host'] and request_header['remote-host']~=nil then 
							if request_header['remote-host']==client_ip then 
								client_ip=tmpe[1]
								client_ip=string.gsub(client_ip," ","")
							end 
						end 
				    end
					if compare_ip_block(client_ip) then
						if tostring(ngx.var.remote_addr) == tostring(client_ip) then
							client_ip = ngx.var.remote_addr
						else
							client_ip = ngx.var.remote_addr
						end
					end
					break;
				end
			end
		end
	end
	if type(client_ip) == 'table' then client_ip = "" end
	if (string.match(client_ip,"^%d+%.%d+%.%d+%.%d+$") == nil and string.match(client_ip,"^[%w:]+$") == nil) or client_ip == 'unknown'  then
		client_ip = ngx.var.remote_addr
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

function get_client_ip()
	local client_ip = "unknown"
	if site_config[server_name] then
		if site_config[server_name]['cdn'] then
			for _,v in ipairs(site_config[server_name]['cdn_header'])
			do
				if request_header[v] ~= nil and request_header[v] ~= "" then
					local header_tmp = request_header[v]
					if type(header_tmp) == "table" then header_tmp = header_tmp[1] end
					client_ip = split_bylog(header_tmp,',')[1]
					if compare_ip_block(client_ip) then
						if tostring(ngx.var.remote_addr) == tostring(client_ip) then
							client_ip = ngx.var.remote_addr
						else
							client_ip = ngx.var.remote_addr
						end
					end
					break;
				end
			end
		end
	end
	if type(client_ip) == 'table' then client_ip = "" end
	if (string.match(client_ip,"^%d+%.%d+%.%d+%.%d+$") == nil and string.match(client_ip,"^[%w:]+$") == nil) or client_ip == 'unknown'  then
		client_ip = ngx.var.remote_addr
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

function split_bylog( str,reps )
	local resultStrList = {}
	string.gsub(str,'[^'..reps..']+',function(w)
		table.insert(resultStrList,w)
	end)
	return resultStrList
end


function split( str,reps )
    if str ==nil then return nil end 
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function(w)
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

function arrip(ipstr)
	if ipstr == 'unknown' then return {0,0,0,0} end
	if string.find(ipstr,':') then return ipstr end
	iparr = split(ipstr,'.')
	iparr[1] = tonumber(iparr[1])
	iparr[2] = tonumber(iparr[2])
	iparr[3] = tonumber(iparr[3])
	iparr[4] = tonumber(iparr[4])
	return iparr
end

function join(arr,e)
	result = ''
	length = arrlen(arr)
	for k,v in ipairs(arr)
	do
		if length == k then e = '' end
		result = result .. v .. e
	end
	return result
end

function arrlen(arr)
	if not arr then return 0 end
	count = 0
	for _,v in ipairs(arr)
	do
		count = count + 1
	end
	return count
end

function select_rule(rules)
	if not rules then return {} end
	new_rules = {}
	for i,v in ipairs(rules)
	do 
		if v[1] == 1 then
			table.insert(new_rules,v[2])
		end
	end
	return new_rules
end



function is_site_config(cname)
	if site_config[server_name] ~= nil then
		if cname == 'cc' then
			return site_config[server_name][cname]['open']
		else
			return site_config[server_name][cname]
		end
	end
	return true
end


function get_boundary()
    local header = request_header["content-type"]
    if not header then return nil end
    if type(header) == "table" then
        return return_message(200,'content-type ERROR')
    end
	if header then
    	if ngx.re.find(header,[[multipart]],'ijo') then
    		if not ngx.re.match(header,'^multipart/form-data; boundary=') then 
    				return return_message(200,'content-type ERROR')
    		end
    	   multipart_data=ngx.re.match(header,'^multipart/form-data; boundary=.+')
    		check_file=ngx.re.gmatch(multipart_data[0],[[=]],'ijo')
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
	        if(arrlen(ret)>=2) then
	            return return_message(200,'multipart/form-data ERROR')
	        end
    		return header
    	else
    		return false
    	end 
    end 
end

local ip_html = read_file_body(config["reqfile_path"] .. '/' .. 'ip.html')
local url_html = read_file_body(config["reqfile_path"] .. '/' .. 'url.html')
local get_html = read_file_body(config["reqfile_path"] .. '/' .. config["get"]["reqfile"])
local post_html = read_file_body(config["reqfile_path"] .. '/' .. config["post"]["reqfile"])
local cookie_html = read_file_body(config["reqfile_path"] .. '/' .. config["cookie"]["reqfile"])
local user_agent_html = read_file_body(config["reqfile_path"] .. '/' .. config["user-agent"]["reqfile"])
local other_html = read_file_body(config["reqfile_path"] .. '/' .. config["other"]["reqfile"])
local cnlist = json.decode(read_file_body(cpath .. '/rule/cn.json'))
local lanlist = json.decode(read_file_body(cpath .. '/rule/lan.json'))
local scan_black_rules = read_file('scan_black')
local ip_black_rules = read_file('ip_black')
local ip_white_rules = read_file('ip_white')
local url_white_rules = read_file('url_white')
local cc_uri_white_rules = read_file('cc_uri_white')
local url_black_rules = read_file('url_black')
local user_agent_rules = select_rule(read_file('user_agent'))
local post_rules = select_rule(read_file('post'))
local cookie_rules = select_rule(read_file('cookie'))
local args_rules = select_rule(read_file('args'))
local url_rules = select_rule(read_file('url'))
local head_white_rules = read_file('head_white')
local referer_local = select_rule(read_file('referer'))
local captcha_num2 = json.decode(read_file_body('/www/server/btwaf/captcha/num2.json'))
local shell_check = json.decode(read_file_body('/www/server/btwaf/shell_check.json'))


function is_min(ip1,ip2)
	if not ip1 then return false end
	if not ip2 then return false end
	n = 0
	for _,v in ipairs({1,2,3,4})
	do
		if  not ip1[v] then return false end 
		if  not ip2[v] then return false end 
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

function is_max(ip1,ip2)
	if not ip1 then return false end
	if not ip2 then return false end
	n = 0
	for _,v in ipairs({1,2,3,4})
	do
		if  not ip1[v] then return false end 
		if  not ip2[v] then return false end 
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


function ip2long(str)
	local num = 0
	if str and type(str)=="string" then
		local o1,o2,o3,o4 = str:match("(%d+)%.(%d+)%.(%d+)%.(%d+)")
		if o1 == nil or o2 == nil or o3 == nil or o4 == nil then return 0 end
		num = 2^24*o1 + 2^16*o2 + 2^8*o3 + o4
	end
    return num
end

function compare_ip(ips)
	if ip == 'unknown' then return true end
	if string.find(ip,':') then return false end
	if not is_max(ipn,ips[2]) then return false end
	if not is_min(ipn,ips[1]) then return false end
	return true
end

function compare_ip2(ips)
	if ip == 'unknown' then return false end
	if string.find(ip,':') then return false end
	if  type(ips[2])~='number' and  type(ips[1])~='number' and  type(ipn2)~='number' then  return false end
	if  ipn2<=ips[2] and ipn2>=ips[1] then return true end 
	return false
end

function get_id()
    local total_path = cpath .. 'total.json'
	local tbody = ngx.shared.btwaf:get(total_path)
	if not tbody then
		tbody = read_file_body(total_path)
		if not tbody then return 0 end
	end
	local total = json.decode(tbody)
	if not total['total'] then total['total'] = 0 end
	total['total'] = total['total'] + 1
    return total['total']
end 

function http_log()
    data=''
    data=method..' ' ..request_uri.. ' '..  'HTTP/1.1\n'
    if not ngx.req.get_headers(2000) then return data end
    for key,valu in pairs(ngx.req.get_headers(2000)) do 
        if type(valu)=='string' then 
            data=data..key..':'..valu..'\n'
        end
		if type(valu) =='table' then
            for key2,val2 in pairs(valu) do
                data=data..key..':'..val2..'\n'
            end 
        end
    end
    data=data..'\n'
    if method ~='GET' then 
        ngx.req.read_body()
        if get_boundary() then
            if ngx.req.get_body_data() then 
                data =data ..ngx.req.get_body_data()
            else
		        if config['http_open'] then 
	            	request_args2=ngx.req.get_body_file()
    		    	request_args2=read_file_body(request_args2)
    		    	data =data ..request_args2
    		    else
    		       data =data ..'\n拦截非法恶意上传文件或者非法from-data传值,该数据包较大系统默认不存储,如需要开启,请在[Nginx防火墙-->全局配置-->HTTP包]'
    		    end
            end
            return data
        else
	        request_args = ngx.req.get_post_args(1000000)
	        
	        --json 记录
	        if ngx.req.get_headers(20000)["content-type"] and  ngx.re.find(ngx.req.get_headers(20000)["content-type"], '^application/json',"oij") then
        		local ok ,request_args = pcall(function()
        			return json.decode(ngx.req.get_body_data())
        		end)
        		if not ok then
        			local check_html = [[<html><meta charset="utf-8" /><title>json格式错误</title><div>请传递正确的json参数</div></html>]]
        			ngx.header.content_type = "text/html;charset=utf8"
        			ngx.say(check_html)
        			ngx.exit(200)
        		end
        		if type(request_args)~='table' then return data end 
        		return data..json.encode(request_args)
            else
	        --x-www-form-urlencoded 传值
	            coun=0
    	        if not request_args then return data end 
        	        for i,v in pairs(request_args) do
        	            if type(v) =='table' then 
        	                for i2,v2 in pairs(v) do 
        	                    if type(v2)=='string' then 
        	                        if coun ==0 then 
        	                            data=data..i..'='..v2
        	                        else
        	                             data=data..'&'..i..'='..v2
        	                        end
        	                        coun=coun+1
        	                    end 
        	                end 
        	            elseif  type(v)=='string' then 
            	            if coun ==0 then 
                                data=data..i..'='..v
                            else
                                 data=data..'&'..i..'='..v
            	            end 
                            coun=coun+1
                        end 
                    end
                    return data
	        end
        end
    else
        return data
    end
end 



function write_log(name,rule)
    
	local count,_ = ngx.shared.drop_ip:get(ip)
	if count then
		ngx.shared.drop_ip:incr(ip,1)
	else
		ngx.shared.drop_ip:set(ip,1,retry_cycle)
	end
	if config['log'] ~= true or is_site_config('log') ~= true then return false end
	local method = ngx.req.get_method()
	if error_rule then 
		rule = error_rule
		error_rule = nil
	end
	
	if is_type then 
		lan_type = is_type
		is_type = nil
	end
	
	if lan_type then 
	    total_count(lan_type)
	else
	    total_count(name)
	end
	
	local logtmp = {ngx.localtime(),ip,method,request_uri,ngx.var.http_user_agent,name,rule,http_log(),lan_type}
	
	local logstr = json.encode(logtmp) .. "\n"
	local count,_ = ngx.shared.drop_ip:get(ip)	
	if count > retry-1 and name ~= 'cc' then
		local safe_count,_ = ngx.shared.drop_sum:get(ip)
		if not safe_count then
			ngx.shared.drop_sum:set(ip,1,86400)
			safe_count = 1
		else
			ngx.shared.drop_sum:incr(ip,1)
		end
		local lock_time = retry_time * safe_count
		if lock_time > 86400 then lock_time = 86400 end
		lan_type='封锁此IP'
		logtmp = {ngx.localtime(),ip,method,request_uri,ngx.var.http_user_agent,name,retry_cycle .. '秒以内累计超过'..retry..'次以上非法请求,封锁'.. lock_time ..'秒',http_log(),lan_type}
		logstr = logstr .. json.encode(logtmp) .. "\n"
		ngx.shared.drop_ip:set(ip,retry+1,lock_time)
		write_drop_ip2('inc',lock_time,rule,name)

	end
	write_to_file(logstr)
	inc_log(name,rule)
end

function write_drop_ip2(is_drop,drop_time,name,rule)
	local filename = cpath .. 'drop_ip.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	if lan_type then lan_type=lan_type end 
	if is_type_rule then lan_type=is_type_rule end 
	local logtmp = {os.time(),ip,server_name,request_uri,drop_time,is_drop,method,ngx.var.http_user_agent,name,rule,http_log()}
	local logstr = json.encode(logtmp) .. "\n"
	fp:write(logstr)
	fp:flush()
	fp:close()
	inc_log(is_drop,rule)
	return true
end

function write_drop_ip(is_drop,drop_time,name)
	local filename = cpath .. 'drop_ip.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	if lan_type then lan_type=lan_type end 
	if is_type_rule then lan_type=is_type_rule end 
	local logtmp = {os.time(),ip,server_name,request_uri,drop_time,is_drop,method,ngx.var.http_user_agent,name,rule,http_log()}
	local logstr = json.encode(logtmp) .. "\n"
	fp:write(logstr)
	fp:flush()
	fp:close()
	inc_log(is_drop,rule)
	return true
end

function inc_log(name,rule)
	local total_path = cpath .. 'total.json'
	local tbody = ngx.shared.btwaf:get(total_path)
	if not tbody then
		tbody = read_file_body(total_path)
		if not tbody then return false end
	end
	local total = json.decode(tbody)
	if not total['sites'] then total['sites'] = {} end
	if not total['sites'][server_name] then total['sites'][server_name] = {} end
	if not total['sites'][server_name][name] then total['sites'][server_name][name] = 0 end
	if not total['rules'] then total['rules'] = {} end
	if not total['rules'][name] then total['rules'][name] = 0 end
	if not total['total'] then total['total'] = 0 end
	total['total'] = total['total'] + 1
	total['sites'][server_name][name] = total['sites'][server_name][name] + 1
	total['rules'][name] = total['rules'][name] + 1
	local total_log = json.encode(total)
	if not total_log then return false end
	ngx.shared.btwaf:set(total_path,total_log)
	if not ngx.shared.btwaf:get('b_btwaf_timeout') then
		write_file(total_path,total_log)
		ngx.shared.btwaf:set('b_btwaf_timeout',1,5)
	end
end

function write_to_file(logstr)
	local filename = config["logs_path"] .. '/' .. server_name .. '_' .. ngx.today() .. '.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	fp:write(logstr)
	fp:flush()
	fp:close()
	return true
end

function is_ssl()
    if(ngx.re.match(request_uri,'^/.well-known/pki-validation/')) then return true end 
    if(ngx.re.match(request_uri,'^/.well-known/acme-challenge/')) then return true end    
end 

function drop_abroad()
	if ip == 'unknown' then return false end
	if string.find(ip,':') then return false end
	if is_ssl() then return false end
	if ip=='91.199.212.132' or ip=='91.199.212.133' or ip=='91.199.212.148' or ip=='91.199.212.151' or ip=='91.199.212.176' then return false end
	if not config['drop_abroad']['open'] or not is_site_config('drop_abroad') then return false end	
	for _,v in ipairs(cnlist)
	do
		if compare_ip2(v) then return false end
	end
	total_count('禁止海外访问')
	ngx.exit(config['drop_abroad']['status'])
	return true
end

function is_ip_lan()
    for k,v in ipairs(lanlist) do 
        if compare_ip2(v) then
            return true
        end 
    end
    return false
end

function drop_china()
	if ip == 'unknown' then return false end
	if string.find(ip,':') then return false end
	if config['drop_china'] ==nil then return false end 
	if site_config[server_name] ==nil then return false end 
	if site_config[server_name]['drop_china'] ==nil then return false end 
	if is_ssl() then return false end
	if not config['drop_china']['open'] or not site_config[server_name]['drop_china'] then return false end
    if config['drop_china']['open'] and site_config[server_name]['drop_china'] then
    	if is_ip_lan() then return false end 
    	for k,v in ipairs(cnlist)
    	do
            if compare_ip2(v) then 
                total_count('禁止国内访问')
               	ngx.exit(config['drop_china']['status'])
            end
    	end
    	return false
    end
    return false
end


function drop()
	local count,_ = ngx.shared.drop_ip:get(ip)
	if not count then return false end
	if count > retry then
		ngx.exit(config['cc']['status'])
		return true
	end
	return false
end

function cc()
	if not config['cc']['open'] or not site_cc then return false end
	if ngx.re.find(uri,'/uc_server/avatar.php') then return false end
	local token = ngx.md5(ip .. '_' .. request_uri)
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
		if (count) > limit then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			local lock_time = (endtime * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			ngx.shared.drop_ip:set(ip,retry+1,lock_time)
			is_type='cc'
			write_log('cc',cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
			write_drop_ip('cc',lock_time,cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
			if not server_name then
				insert_ip_list(ip,lock_time,os.time(),'1111')
			else
				insert_ip_list(ip,lock_time,os.time(),server_name)
			end
			
			ngx.exit(config['cc']['status'])
			return true
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,cycle)
	end
	return false
end

-- function cc_html_dan()
-- 	if uri == nil then return false end
-- 	if string.find(uri,'html$') then 
-- 		local cache_token =ip .. '_' .. server_name .. 'html'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 			ngx.shared.btwaf:incr(cache_token,1)
-- 		end
-- 	elseif string.find(uri,'php$') then
-- 		local cache_token =ip .. '_' .. server_name .. 'php'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 			ngx.shared.btwaf:incr(cache_token,1)
-- 		end
		
-- 	elseif string.find(uri,'js$') then
-- 		local cache_token =ip .. '_' .. server_name .. 'js'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 			ngx.shared.btwaf:incr(cache_token,1)
-- 		end

-- 	elseif string.find(uri,'css$') then
-- 		local cache_token =ip .. '_' .. server_name .. 'css'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 				ngx.shared.btwaf:incr(cache_token,1)
-- 		end
	
-- 	elseif string.find(uri,'png$') then
-- 		local cache_token =ip .. '_' .. server_name .. 'png'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 				ngx.shared.btwaf:incr(cache_token,1)
-- 		end

-- 	elseif string.find(uri,'jpg$') then
-- 		local cache_token =ip .. '_' .. server_name .. 'png'
-- 		if not ngx.shared.btwaf:get(cache_token) then 
-- 			ngx.shared.btwaf:set(cache_token,1,60)
-- 		else
-- 				ngx.shared.btwaf:incr(cache_token,1)
-- 		end

-- 	else 
-- 		if not  cc_increase_static() then  
-- 			local cache_token =ip .. '_' .. server_name 
-- 			if not ngx.shared.btwaf:get(cache_token) then 
-- 				ngx.shared.btwaf:set(cache_token,1,60)
-- 			else
-- 					ngx.shared.btwaf:incr(cache_token,1)
-- 			end
-- 		end
-- 	end
-- end

function cc_increase()
	if not config['cc']['open'] or not site_cc then return false end
	if not site_config[server_name] then return false end
	if not site_config[server_name]['cc']['increase'] then return false end
	local cache_token = ngx.md5(ip .. '_' .. server_name)
	if ngx.shared.btwaf:get(cache_token) then  return false end
	if cc_uri_white() then
		ngx.shared.btwaf:delete(cache_token .. '_key')
		ngx.shared.btwaf:set(cache_token,1,180)
		return false 
	end
	if security_verification() then return false end
	send_check_heml(cache_token)
end

-- function cc_increase_wuheng()
-- 	if not config['cc']['open'] or not site_cc then return false end
-- 	if not site_config[server_name] then return false end
-- 	if not site_config[server_name]['increase_wu_heng'] then return false end
-- 	local ip_token =ip .. '_' .. server_name 
-- 	local cache_token = ngx.md5(ip .. '_' .. server_name)
-- 	local html_token =ip .. '_' .. server_name .. 'html'
-- 	local php_token =ip .. '_' .. server_name .. 'php'
-- 	local js_token =ip .. '_' .. server_name .. 'js'
-- 	local css_token =ip .. '_' .. server_name .. 'css'
-- 	local png_token =ip .. '_' .. server_name .. 'png'
-- 	local jpg_token =ip .. '_' .. server_name .. 'jpg'
-- 	if ngx.shared.btwaf:get(ip_token) then 
-- 		if ngx.shared.btwaf:get(ip_token)>3 then 
-- 			if ngx.shared.btwaf:get(js_token) == nil  then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end
-- 	end
-- 	if ngx.shared.btwaf:get(html_token) then   
-- 		if ngx.shared.btwaf:get(html_token)>3 then 
-- 			if ngx.shared.btwaf:get(js_token) == nil  or ngx.shared.btwaf:get(css_token)==nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- 	if ngx.shared.btwaf:get(php_token) then   
-- 		if ngx.shared.btwaf:get(php_token)>3 then 
-- 			if not ngx.shared.btwaf:get(js_token) == nil  or  not ngx.shared.btwaf:get(png_token) == nil or not ngx.shared.btwaf:get(css_token) == nil or not ngx.shared.btwaf:get(jpg_token) == nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- 	if ngx.shared.btwaf:get(js_token) then   
-- 		if ngx.shared.btwaf:get(js_token)>10 then 
-- 			if ngx.shared.btwaf:get(html_token) == nil  or ngx.shared.btwaf:get(php_token)==nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- 	if ngx.shared.btwaf:get(css_token)  then   
-- 		if ngx.shared.btwaf:get(css_token)>10 then 
-- 			if ngx.shared.btwaf:get(html_token) == nil  or  ngx.shared.btwaf:get(php_token)==nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- 	if ngx.shared.btwaf:get(jpg_token)  then   
-- 		if ngx.shared.btwaf:get(jpg_token)>10 then 
-- 			if ngx.shared.btwaf:get(html_token) == nil  or ngx.shared.btwaf:get(php_token)==nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- 	if  ngx.shared.btwaf:get(png_token)  then   
-- 		if ngx.shared.btwaf:get(png_token)>10 then 
-- 			if ngx.shared.btwaf:get(html_token) == nil  or ngx.shared.btwaf:get(php_token)==nil then 
-- 				check_qingqiu(cache_token)
-- 			end
-- 		end 
-- 	end
-- end

-- function check_qingqiu(cache_token)
-- 	if ngx.shared.btwaf:get(cache_token) then  return false end
-- 	if cc_uri_white() then
-- 		ngx.shared.btwaf:delete(cache_token .. '_key')
-- 		ngx.shared.btwaf:set(cache_token,1,60)
-- 		return false 
-- 	end
-- 	if security_verification() then return false end
-- 	send_check_heml(cache_token)
-- end

function send_check_heml(cache_token)
	local check_key = tostring(math.random(10000000,99999999))
	ngx.shared.btwaf:set(cache_token .. '_key',check_key,60)
	local vargs = '&btwaf='
	local sargs = string.gsub(request_uri,'.?btwaf=.*','')
	if not string.find(sargs,'?',1,true) then vargs = '?btwaf=' end
	local safe_count = ngx.shared.drop_ip:get(ip)
	if not safe_count then
		ngx.shared.drop_ip:set(ip,1,endtime)
		safe_count = 1
	else
		ngx.shared.drop_ip:incr(ip,1)
		safe_count = safe_count +1
	end

	if safe_count >= retry then
		local safe_count2,_ = ngx.shared.drop_sum:get(ip)
		if not safe_count2 then safe_count2=1 end
		retry_time = site_config[server_name]['retry_time']
		local lock_time = (retry_time * safe_count2)
		if lock_time > 86400 then lock_time = 86400 end
		if not server_name then
			insert_ip_list(ip,lock_time,os.time(),'1111')
		else
			insert_ip_list(ip,lock_time,os.time(),server_name)
		end
		is_type='cc'
		write_log('cc','累计超过'.. retry ..'次验证失败,封锁' .. lock_time .. '秒')
		write_drop_ip('cc',lock_time,'累计超过'.. retry ..'次验证失败,封锁' .. lock_time .. '秒')
	end

	local check_html = [[<html><meta charset="utf-8" /><title>检测中</title><div>跳转中</div></html>
<script> window.location.href ="]] .. sargs .. vargs .. check_key .. [["; </script>]]
	ngx.header.content_type = "text/html;charset=utf8"
	ngx.say(check_html)
	ngx.exit(200)
end

function security_verification()
	if  not uri_request_args['btwaf'] then return false end
	local cache_token = ngx.md5(ip .. '_' .. server_name)
	check_key = ngx.shared.btwaf:get(cache_token .. '_key')
	if check_key == uri_request_args['btwaf'] then
		ngx.shared.btwaf:delete(cache_token .. '_key')
		ngx.shared.btwaf:set(cache_token,1,180)
		return true
	end
	return false
end

function scan_black()
	if not config['scan']['open'] or not is_site_config('scan') then return false end
	if is_ngx_match(scan_black_rules['cookie'],request_header['cookie'],false) then
		write_log('scan','regular')
		ngx.exit(config['scan']['status'])
		return true
	end
	if is_ngx_match(scan_black_rules['args'],request_uri,false) then
		write_log('scan','regular')
		ngx.exit(config['scan']['status'])
		return true
	end
	for key,value in pairs(request_header)
	do
		if is_ngx_match(scan_black_rules['header'],key,false) then
			write_log('scan','regular')
			ngx.exit(config['scan']['status'])
			return true
		end
	end
	return false
end


function ip_black()
	for _,rule in ipairs(ip_black_rules)
	do
		if compare_ip2(rule) then 
			ngx.exit(config['cc']['status'])
			return true 
		end
	end
	return false
end

function ip_white()
	--if ngx.shared.btwaf_data:get(ip .. 'baimingdna') then return true end
	if ngx.var.server_name =='_' and ip =='127.0.0.1' then return false end
	for _,rule in ipairs(ip_white_rules)
	do
		if compare_ip2(rule) then 
			return true 
		end
	end
	return false
end

function url_white()
	if ngx.var.document_root=='/www/server/phpmyadmin' then return true end
	if is_ngx_match(url_white_rules,request_uri,false) then
        url_data=split2(request_uri,'?')
        if not url_data then url_data=request_uri end 
        if not url_data[1] then 
            url_data=request_uri 
        else
            url_data=url_data[1]
        end
        if ngx.re.match(url_data,'/\\.\\./') then return false end
		return true
	end
	if site_config[server_name] ~= nil then
		if is_ngx_match(site_config[server_name]['url_white'],request_uri,false) then
            url_data=split2(request_uri,'?')
            if not url_data then url_data=request_uri end 
            if not url_data[1] then 
                url_data=request_uri 
            else
                url_data=url_data[1]
            end
            if ngx.re.match(url_data,'/\\.\\./') then return false end
    		return true
    	end
	end
	return false
end

function url_black()
	if is_ngx_match(url_black_rules,request_uri,false) then
		ngx.exit(config['get']['status'])
		return true
	end
	return false
end

function head()
	if not config['get']['open'] or not is_site_config('get') then return false end
	if method ~= 'HEAD' then return false end
	for _,v in ipairs(head_white_rules)
	do
		if ngx_match(uri,v,"isjo") then
			return false
		end
	end
	if ua_whilie2(request_header['user-agent']) then return false end 
	write_log('head','禁止HEAD请求')
	ngx.shared.btwaf:set(ip,retry,endtime)
	write_drop_ip('head',endtime)
	ngx.exit(444)
end

function user_agent()
	if not config['user-agent']['open'] or not is_site_config('user-agent') then return false end	
	if is_ngx_match(user_agent_rules,request_header['user-agent'],'user_agent') then
	    
		lan_ip('user_agent','UA存在问题已经被系统拦截。并封锁IP')
		return true
	end
	return false
end

function de_dict (l_key,l_data)
	if type(l_data) ~= "table" then return l_data end
	if arrlen(l_data) == 0 then return l_data end
	if not l_data then return false end
	local r_data = {}
	if arrlen(l_data) >= 500 then 
	    is_type='POST参数'
		lan_ip('args','非法请求')
		return true
	end
	for li,lv in pairs(l_data)
	do
		r_data[l_key..tostring(li)] = lv
	end
	return r_data
end

local function _process_json_args(json_args,t)
		if type(json_args)~='table' then return {} end
        local t = t or {}
        for k,v in pairs(json_args) do
                if type(v) == 'table' then
                        for _k,_v in pairs(v) do
                                if type(_v) == "table" then
                                    t = _process_json_args(_v,t)

                                else
                                        if type(t[k]) == "table" then
                                                table.insert(t[k],_v)

                                        elseif type(t[k]) == "string" then
                                                local tmp = {}
                                                table.insert(tmp,t[k])
                                                table.insert(tmp,_v)
                                                t[k] = tmp
                                        else

                                        t[k] = _v
                                        end
                                end

                        end
                else
                                         if type(t[k]) == "table" then
                                                table.insert(t[k],v)
                                        elseif type(t[k]) == "string" then
                                                local tmp = {}
                                                table.insert(tmp,t[k])
                                                table.insert(tmp,v)
                                                t[k] = tmp
                                        else

                                        t[k] = v
                                        end
                end
        end
        return t
end

function ReadFileHelper4(str)
	 if type(str)~='string' then return str end
	 res = string.gsub(str, "@", "")
    return res
end


function libinjection_chekc(requires_data)
	if type(requires_data)~='table' then return false end 
	for k,v in pairs(requires_data) do
		if continue_key(k) then
			if type(v)=='string' then
				is_body_intercept(v)
			 	if config['post_is_sql']  and is_site_config('post_is_sql') then 
					local issqli, fingerprint = libinjection.sqli(tostring(ReadFileHelper4(v)))
					local issqli2, fingerprint = libinjection.sqli(tostring(ReadFileHelper4(k)))
					if issqli or issqli2 then
						error_rule = '语义分析分析出sql注入' .. ' >> ' .. tostring(k)..'='..tostring(v)..' >> '..tostring(v)
						is_type='SQL注入'
						return true 
					end 
				end 
				if config['post_is_xss'] then
					local isxss = libinjection.xss(tostring(v))
					if isxss then
						if not ngx.shared.btwaf_data:get(ip..'xss') then 
							ngx.shared.btwaf_data:set(ip..'xss',1,360)
						else
							ngx.shared.btwaf_data:incr(ip..'xss',1)
						end
						if ngx.shared.btwaf_data:get(ip..'xss')>=6 then
							error_rule = '语义分析分析出xss跨站攻击' .. ' >> ' .. tostring(k)..'='..tostring(v)..' >> '..tostring(v)
							is_type="XSS攻击"
							return true
						end
					end
				end
			end
		else
			if type(v)=='string' then
				is_body_intercept(v)
			end
		end
	end 
	return false
end

function select_rule2(is_type,rule)
    if is_type =='post' or is_type=='args' or is_type=='url' then
        local post_rules2 =read_file(is_type)
    	if not post_rules2 then return nil end
    	for i,v in ipairs(post_rules2)
    	do 
    		if v[1] == 1 then
    		    if v[2]==rule then 
    		        return v[3]
    		        
    		    end
    		end
    	end
    end
	return nil
end

function is_type_return(is_type,rule)
    if is_type ~='post' and is_type~='args' and is_type~='url'  then return nil end 
    data=select_rule2(is_type,rule)
    if data==nil then return nil end 
    if data=='目录保护1' or data=='目录保护2' or data=='目录保护3' then return "目录保护" end 
    if data=='PHP流协议过滤1' then return "PHP流协议" end 
    if  data=='一句话*屏蔽的关键字*过滤1' or  data=='一句话*屏蔽的关键字*过滤2' or data=='一句话木马过滤1' or data=='一句话木马过滤3' or data=='一句话*屏蔽的关键字*过滤3' or data=='菜刀流量过滤' then return 'PHP函数' end
    if data=='SQL注入过滤2' or data=='SQL注入过滤1' or data=='SQL注入过滤3' or data=='SQL注入过滤4' or data=='SQL注入过滤5' or data=='SQL注入过滤6'  then return "SQL注入"  end 
    if data=='SQL注入过滤7' or data=='SQL注入过滤9' or data=='SQL注入过滤8' or data=='SQL注入过滤10' or data=='test' then return 'SQL注入' end 
    if data=='SQL报错注入过滤01' or data=='SQL报错注入过滤02' then return 'SQL注入' end
    if data=='一句话木马过滤5' or data=='一句话木马过滤4' then return 'PHP脚本过滤' end
    if data=="" then return 'SQL注入' end
    if data=='XSS过滤1' then return 'XSS攻击' end
    if data=='ThinkPHP payload封堵' then return 'ThinkPHP攻击' end
    if data=='文件目录过滤1' or data=='文件目录过滤2' or data=='文件目录过滤3' then return '目录保护' end
    if data=='PHP脚本执行过滤1' or data=='PHP脚本执行过滤2' then return 'PHP脚本过滤' end
    return data
end 


function is_ngx_match_urlencoded(rules,sbody,rule_name,disable,threshold)
	if rules == nil or sbody == nil then return false end
	if type(sbody) == "string" then
		sbody = {sbody}
	end
	if type(rules) == "string" then
		rules = {rules}
	end
	for k,body in pairs(sbody)
    do  
		if continue_key(k)  then
			for i,rule in ipairs(rules)
			do
				if site_config[server_name] and rule_name then
					local n = i - 1
					for _,j in ipairs(site_config[server_name]['disable_rule'][rule_name])
					do
						if n == j then
							rule = ""
						end
					end
				end
				for _,num in pairs(disable) do
					if num == i or i > threshold then 
						if body and rule ~="" then
							if type(body) == "string" then
								if ngx_match(ngx.unescape_uri(body),rule,"isjo") then
									if method ~="POST" and  rule=="'$" then
									    return false
									end
									is_type=is_type_return(rule_name,rule)
									error_rule = rule .. ' >> ' .. k .. '=' .. body ..' >> ' .. body
									return true
								end
							end
							if type(k) == "string" then
								if ngx_match(ngx.unescape_uri(k),rule,"isjo") then
								    is_type=is_type_return(rule_name,rule)
									error_rule = rule .. ' >> ' .. k.. ' >> ' .. k
									return true
								end
							end
						end
					end
				end
			end
		end
	end
	return false
end

function post_urlencoded(request_args)
	if ngx.shared.btwaf_data:get(ip..'post') then 
		disable={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}
	else
		disable={1,2,3,4,5,6,7,8,9,12,13,21,23}
	end 
	if is_ngx_match_urlencoded(post_rules,request_args,'post',disable,23) then
		write_log('post','regular')
		return_html(config['post']['status'],post_html)
	end 
	if libinjection_chekc(request_args) then
		ngx.shared.btwaf_data:set(ip..'post','1',360)
		write_log('post','regular')
		return_html(config['post']['status'],post_html)
	end

end



function post()
	if not config['post']['open'] or not is_site_config('post') then return false end	
	if method == "GET" then return false end
	if post_referer() then return true end
	content_length=tonumber(request_header['content-length'])
	if content_length == nil then return false end
	local content_type = ngx.req.get_headers(20000)["content-type"]
	if not content_type then return false end 
	if type(content_type)~='string' then 
		return_error(17)
	end 
	if content_type and ngx.re.find(content_type, 'multipart',"oij") then return false end 
	ngx.req.read_body()
	request_args = ngx.req.get_post_args(1000000)
	if not request_args then
		if content_length >10000 then 
		    request_uri22=split2(request_uri,'?')
		    request_uri22=request_uri22[1]
			local check_html = [[<html><meta charset="utf-8" /><title>Nginx缓冲区溢出</title><div>宝塔WAF提醒您,Nginx缓冲区溢出,传递的参数超过接受参数的大小,出现异常,<br>第一种解决方案:把当前url-->]]..'^'..request_uri22..[[加入到URL白名单中,如有疑问请联系官方运维QQ</br>第二种解决方案:面板-->nginx管理->性能调整-->client_body_buffer_size的值调整为10240K 或者5024K(PS:可能会一直请求失败建议加入白名单)</br></div></html>]]
			ngx.header.content_type = "text/html;charset=utf8"
			ngx.say(check_html)
			ngx.exit(200)
		end 
		return true
	end
	list_data={}
	if type(request_args)=='table' then
		for k,v in pairs(request_args)
		do
			if type(v)=='table' then
				table.insert(list_data,de_dict(k,v))
			end
            if type(v)=='string' then
				if not  string.find(v,'^data:.+/.+;base64,') then
					if (#v) >=200000 then
						write_log('post',k..'     参数值长度超过20w已被系统拦截')
						return_html(config['post']['status'],post_html)
						return true
					end
				else
					kkkkk=ngx.re.match(v,'^data:.+;base64,','ijo')
					if  kkkkk then 
						if kkkkk[0] then 
							if ngx.re.match(kkkkk[0],'php') or ngx.re.match(kkkkk[0],'jsp') then 
							    is_type='webshell防御'
								write_log('post','拦截Bae64上传php文件')
								return_html(config['post']['status'],post_html)
							end 
						end
					end
				end
			end
		end
	end
	if content_type and  ngx.re.find(content_type, '^application/json',"oij") and ngx.req.get_headers(20000)["content-length"] and tonumber(ngx.req.get_headers(20000)["content-length"]) ~= 0 then
		local ok ,request_args = pcall(function()
			return json.decode(ngx.req.get_body_data())
		end)
		if not ok then
			local check_html = [[<html><meta charset="utf-8" /><title>json格式错误</title><div>请传递正确的json参数</div></html>]]
			ngx.header.content_type = "text/html;charset=utf8"
			ngx.say(check_html)
			ngx.exit(200)
		end
		if type(request_args)~='table' then return false end 
		request_args=_process_json_args(request_args)
		return post_urlencoded(request_args)
	else
		if list_data then 
			if arrlen(list_data)>=1 then 
				for i2,v2 in ipairs(list_data) do 
					post_urlencoded(v2)
					request_args=_process_json_args(v2,request_args)
				end 
			else 
				request_args=_process_json_args(list_data,request_args)
			end 
		else
			request_args =_process_json_args(request_args)
		end
		if count_sieze(request_args)>=800 then
		    is_type='POST参数'
			error_rule = '参数太多POST传递的参数数量超过800,拒绝访问,如有误报请点击误报'
		    write_log('post','参数太多POST传递的参数数量超过800,拒绝访问,如有误报请点击误报')
		    return_html_data('网站防火墙','您的请求带有不合法参数，已被网站管理员设置拦截','网站防火墙提醒您POST传递的参数数量超过800,拒绝访问','点击误报')
		end
	    post_urlencoded(request_args)
	end
	return false
end

function chekc_data_table(data)
	if type(data) ~= 'table' then return false end
	for k,v in ipairs(data)
	do
		return return_message(200,type(v))

	end
	return false
end

function lan_ip(type,name)
	local safe_count,_ = ngx.shared.drop_sum:get(ip)
	if not safe_count then
		ngx.shared.drop_sum:set(ip,1,86400)
		safe_count = 1
	else
		ngx.shared.drop_sum:incr(ip,1)
	end
	local lock_time = (endtime * safe_count)
	if lock_time > 86400 then lock_time = 86400 end
	ngx.shared.drop_ip:set(ip,retry+1,lock_time)
	local method = ngx.req.get_method()
	if error_rule then 
		rule = error_rule
		error_rule = nil
	end
	if is_type then 
		is_type_rule = is_type
		is_type = nil
	end
	
	if is_type_rule then 
	    total_count(is_type_rule)
	else
	    if type ~='user_agent' then total_count(type) end
	end
	local logtmp = {ngx.localtime(),ip,method,request_uri,ngx.var.http_user_agent,type,name,http_log(),is_type_rule}
	local logstr = json.encode(logtmp) .. "\n"
	
	write_to_file(logstr)
	inc_log(type,rule)
	if type =='args' or type=='post' or type =='inc' then 
		write_drop_ip2('inc',lock_time,name,rule)
	else
		write_drop_ip2(type,lock_time,name,rule)
	end 
	ngx.exit(config['cc']['status'])
end

function disable_upload_ext(ext)
	if not ext then return false end
	if type(ext)=='string' then 
		ext = string.lower(ext)
		if ngx.re.match(ext,'.user.ini') or ngx.re.match(ext,'.htaccess') or ngx.re.match(ext,'php') or ngx.re.match(ext,'jsp') then 
		    is_type='webshell防御'
	        lan_ip('disable_upload_ext','上传非法文件被系统拦截,并且被封锁IP')
		    return true
		end
	end 
	if not site_config[server_name] then return false end 
	disa=site_config[server_name]['disable_upload_ext']
	ret={}
	for _,k  in ipairs(disa) 
	do 
		if k~='so' then 
			table.insert(ret,k)
		end
	end
	if is_ngx_match(ret,ext,'post') then
	    is_type='webshell防御'
		lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP2'..' >> '..ext)
		return true
	end
end

function return_error(int_age)
    is_type='http包非法'
	lan_ip('post','http包非法,并且被封锁IP,如果自定义了from-data可能会导致误报。如果大量出现当前问题。请在全局设置中关闭from_data协议规范'..int_age)
end 

function disable_upload_ext2(ext)
	if not ext then return false end
    if type(ext)~='table' then return false end 
	for i,k in pairs(ext) do 
	    for i2,k2 in pairs(k) do
	       check_file=ngx.re.gmatch(k2,[[filename=]],'ijo')
	       ret={}
	       while true do
    		    local m, err = check_file()
    	      	if m then 
    	      		table.insert(ret,m)
    	      	else
    	      		break
    	      	end 
	       end
            if arrlen(ret)>1 then 
                return_error(1)
            end
    	    if not ngx.re.match(k2,[[filename=""]],'ijo') and  not ngx.re.match(k2,[[filename=".+"]],'ijo') then 
				return_error(2)
    	    else 
    	        k2 = string.lower(k2)
    	        if site_config[server_name] ==nil then return false end 
	        	disa=site_config[server_name]['disable_upload_ext']
            	if is_ngx_match(disa,k2,'post') then
            	    is_type='恶意上传'
            		lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP3'..' >> '..k2)
            		return true
            	end
    	    end
		
    	 end 
	end 
	
end


function  from_data(data,data2,data3)
	if arrlen(data) ==0 then return false end 
	local count=0
	for k,v in pairs(data) do
	    if ngx.re.match(v[0],'filename=') then 
	        if not ngx.re.match(v[0],'Content-Disposition: form-data; name="[^"]+"; filename=""\r*$') then 
	            if not ngx.re.match(v[0],'Content-Disposition: form-data; name="[^"]+"; filename="[^"]+"\r*$') then 
	                is_type='恶意上传'
	                return_error2(v[0],'4.5')
	            end
	        end
	        count=count+1
	        disable_upload_ext(v[0])
	    end
	    if config['from_data'] then 
			if not ngx.re.match(v[0],'filename=') and  not ngx.re.match(v[0],'Content-Disposition: form-data; name="[^"]+"\r*$')  then 
			    is_type='http包非法'
				return_error2(v[0],'5')
			end
		end
	end
    len_count=arrlen(data2)+arrlen(data3)
	if count ~=len_count then
		   is_type='http包非法'
	       return_error2('','6')
	 end 
end

function post_data()
	if not config['post']['open'] or not is_site_config('post') then return false end
	if method ~= "POST" then return false end
	content_length=tonumber(request_header['content-length'])
	if not content_length then return false end
	if content_length >108246867 then return false end 
	local boundary = get_boundary()
	if boundary then
		ngx.req.read_body()
		local data = ngx.req.get_body_data()
		if not data then 
		   data=ngx.req.get_body_file()
		   if data==nil then return false end 
            data=read_file_body(data) 
		end
		if not data then return false end
		data233=string.gsub(data,'\r','')
		local tmp4 = ngx.re.gmatch(data,[[Content-Disposition.+]],'ijo')
		local tmp5 = ngx.re.gmatch(data,[[Content-Disposition: form-data; name=".+"; filename=".+"\r\nContent-Type:]],'ijo')
		local tmp6 = ngx.re.gmatch(data,[[Content-Disposition: form-data; name=".+"; filename=""\r\nContent-Type:]],'ijo')
		ret3={}
		while true do local m, err = tmp4() if m then table.insert(ret3,m) else break end  end
		ret5={}
		while true do local m, err = tmp5() if m then  table.insert(ret5,m) else break end end
	    ret6={}
		while true do  local m, err = tmp6() if m then  table.insert(ret6,m) else break end  end
		from_data(ret3,ret5,ret6)
		local tmp2 = ngx.re.gmatch(data,[[Content-Disposition.+filename=.+]],'ijo')
		local tmp3 = ngx.re.gmatch(data,[[Content-Disposition.+\s*f\r*\n*o\r*\n*r\r*\n*m\r*\n*-\r*\n*d\r*\n*a\r*\n*t\r*\n*a\r*\n*\s*;\r*\n*\s*n\r*\n*a\r*\n*m\r*\n*e=\r*\n*.+;\s*f\n*\s*\r*i\n*\s*\r*l\n*\s*\r*e\n*\s*\r*n\n*\s*\r*a\n*\s*\r*m\n*\s*\r*e\n*\s*\r*=.+\n*\s*\r*]],'ijo')
		ret={}
		while true do local m, err = tmp2() if m then  table.insert(ret,m) else break end  end
		ret2={}
		while true do local m, err = tmp3() if m then  table.insert(ret2,m) else break end  end
		disable_upload_ext2(ret2)
	    if arrlen(ret)==0 and arrlen(ret2)>0 then 
	        return_error(3)
	    end
	    ret=gusb_string(ret)
		for k,v in pairs(ret) do 
			disable_upload_ext(v)
		end
		local tmp2=ngx.re.match(data,[[Content-Type:[^\+]{100}]],'ijo')
		if tmp2 and tmp2[0] then 
			data_in_php(tmp2[0])
		end
		av=ngx.re.match(boundary,"=.+")
		if not av then 
			write_log('post','content_type_null')
			return_html(config['post']['status'],post_html)
		end
		header_data=ngx.re.gsub(av[0],'=','')
		if #header_data>200 then 
		    return_error(5)
		end
		
	    data=string.gsub(data,'\n','')
		data=string.gsub(data,'\t','')
		local tmp_pyload2 = ngx.re.match(data,'Content-Disposition:.+\r--','ijo')
 		if tmp_pyload2==nil then return false end 
 		tmpe_data2=split2(tmp_pyload2[0],header_data)
		if arrlen(tmpe_data2)>0 then
			if config['from_data'] then 
	    		disable_upload_ext3(tmpe_data2,1)
	    	end
		end
		data=string.gsub(data,'\r','')
		local tmp_pyload = ngx.re.match(data,'Content-Disposition:.+Content-Type:','ijo')
         if tmp_pyload==nil then return false end 
		tmpe_data=split2(tmp_pyload[0],header_data)
		if arrlen(tmpe_data)>0 then 
		    disable_upload_ext3(tmpe_data,2)
		end 
	end
	return false
end



function split2(input, delimiter)
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


function  return_error2(rule,rule2)
    is_type="http包非法"
	error_rule = 'from-data 请求异常,拒绝访问,如有误报请点击误报'..' >> '..rule..' >> '..rule2
	write_log('post','from-data 请求异常,拒绝访问,如有误报请点击误报')
    local check_html = [[<html><meta charset="utf-8" /><title>from-data请求error</title><div>宝塔WAF提醒您,from-data 请求异常,拒绝访问,如有误报请点击误报</div></html>]]
		ngx.header.content_type = "text/html;charset=utf8"
		ngx.say(check_html)
		ngx.exit(200)

end 

function disable_upload_ext3(ext,check)
	if not ext then return false end
    if type(ext)~='table' then return false end 
    for i2,k2 in pairs(ext) do
        check_file=ngx.re.gmatch(k2,[[filename=]],'ijo')
       ret={}
      while true do
    	    local m, err = check_file()
          	if m then 
          		table.insert(ret,m)
          	else
          		break
          	end 
       end
        if arrlen(ret)>1 then 
            return_error(6)
        end
        if check==1 then
             if arrlen(ret)==0 then 
            	if not k2 then return false end 
				kkkkk=ngx.re.match(k2,[[Content-Disposition:.{200}]],'ijo')
			    if not kkkkk then 
                	if not ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r]],'ijom') or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r;name=]],'ijo')  or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r;\s*\r*\n*n\s*\r*\n*a\s*\r*\n*m\s*\r*\n*e\s*\r*\n*=]],'ijo') or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\s*;]],'ijo') then 
                		k2=string.gsub(k2,'\r','')
                		if ngx.re.match(k2,[[filename=]],'ijo') then 
                		    is_type='恶意上传'
                		    return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP1') 
                		end 
                		return return_error2('','1')
                	end
                else
                    k2=kkkkk[0]
                    if not ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r]],'ijom') or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r;name=]],'ijo')  or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\r;\s*\r*\n*n\s*\r*\n*a\s*\r*\n*m\s*\r*\n*e\s*\r*\n*=]],'ijo') or ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"\r\s*;]],'ijo') then 
                		k2=string.gsub(k2,'\r','')
                		if ngx.re.match(k2,[[filename=]],'ijo') then 
                		    is_type='恶意上传'
                		    return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP2') 
                		end
                		return return_error2('','2')
                	end
                end
                if k2 then 
                	k2=string.gsub(k2,'\r','')
            		if ngx.re.match(k2,[[filename=]],'ijo') then 
            		    is_type='恶意上传'
            		    return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP3') 
            	    end 
                end
            	if ngx.re.match(k2,[[Content-Disposition: form-data; name="(.+)"\r]],'ijos') then 
            	    tttt=ngx.re.match(k2,[[Content-Disposition: form-data; name="(.+)"\r\s]],'ijos')
                    if tttt==nil then return false end 
                    if #tttt[0] >200 then return false end
                    if tttt[1] ==nil then return false end 
                    tttt[1]=string.gsub(tttt[1],'\n','')
		            tttt[1]=string.gsub(tttt[1],'\t','')
		            tttt[1]=string.gsub(tttt[1],'\r','')
		            if ngx.re.match(tttt[1],'name=','ijo') then return return_error2(tttt[1],tttt[1]) end
            	end
            	if ngx.re.match(k2,[[\r\r(.+)\r\r]],'ijos') then 
            	    tttt=ngx.re.match(k2,[[\r\r(.+)\r\r]],'ijos')
                    if tttt==nil then return false end 
                    if #tttt[0] >200 then return false end 
                    if tttt[1] ==nil then return false end 
                    tttt[1]=string.gsub(tttt[1],'\n','')
		            tttt[1]=string.gsub(tttt[1],'\t','')
		            tttt[1]=string.gsub(tttt[1],'\r','')
		            if ngx.re.match(tttt[1],'name=','ijo') then return return_error2(tttt[1],tttt[1]) end
            	end
			else
				if not k2 then return false end 
				k2=string.gsub(k2,'\r','')
				kkkkk=ngx.re.match(k2,[[Content-Disposition:.{200}]],'ijo')
				if not kkkkk then 
				    k3=ngx.re.match(k2,[[Content-Disposition:.+Content-Type:]])
				    is_type='恶意上传'
				    if not k3 then return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP4') end 
				    
				    if not ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"; filename=""Content-Type:]],'ijo') and not  ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"; filename=".+"Content-Type:]],'ijo') then 
				        is_type='恶意上传'
            	        return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP5')
            	    end 
				else
				    k3=ngx.re.match(kkkkk[0],[[Content-Disposition:.+Content-Type:]])
				    if not k3 then 
				        --return lan_ip('disable_upload_ext','上传的文件名非法,文件名过长,或者为空') 
				        return false
				        end 
					if not ngx.re.match(k3[0],[[Content-Disposition: form-data; name=".+"; filename=""Content-Type:]],'ijo') and not  ngx.re.match(k3[0],[[Content-Disposition: form-data; name=".+"; filename=".+"Content-Type:]],'ijo') then
					    is_type='恶意上传'
            	        return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP7')
            	    end
				end
				if site_config[server_name] ==nil then return false end 
            	disa=site_config[server_name]['disable_upload_ext']
            	if is_ngx_match(disa,k3,'post') then
            	    is_type='恶意上传'
            		lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP4')
            	end
            	if #k3[0] >200 then 
        	       ret10={}
            	   local tmp10 = ngx.re.gmatch(k3[0],'form-data')
            	   while true do local m, err = tmp10() if m then  table.insert(ret10,m) else break end  end
                   if tonumber(arrlen(ret10)) >1 then return false end 
                   if ngx.re.match(k3[0],'--$') then return false end
                   return return_message(200,'error1->The upload file name is too long')
        	   	end
            	local tmp8 = ngx.re.gmatch(k3[0],'\"')
            	local tmp9 = ngx.re.gmatch(k3[0],'=')
            	local tmp10 = ngx.re.gmatch(k3[0],';')
                ret8={}
                ret9={}
                ret10={}
                while true do local m, err = tmp8() if m then  table.insert(ret8,m) else break end  end
                while true do local m, err = tmp9() if m then  table.insert(ret9,m) else break end  end
                while true do local m, err = tmp10() if m then  table.insert(ret10,m) else break end  end
                if tonumber(arrlen(ret9))~=2 and tonumber(arrlen(ret8))~=4 and tonumber(arrlen(ret10))~=2 then
                    return_error2('','10')
                end 
                --return return_message(200,k3)
        --         error_rule = '非法文件上传请求。已经被系统拦截'
        --         is_type='恶意上传'
    		  --  write_log('post','非法文件上传请求。已经被系统拦截')
    		  --  local check_html = [[<html><meta charset="utf-8" /><title>非法请求</title><div>宝塔WAF提醒您,文件上传参数错误。文件名或者参数中不能存在分号、等号、和双引号。如有误报请点击误报</div></html>]]
    				-- ngx.header.content_type = "text/html;charset=utf8"
    				-- ngx.say(check_html)
    				-- ngx.exit(200)
             end
            
        else 
            if arrlen(ret)==0 then
                return false
            else 
                kkkkk=ngx.re.match(k2,[[Content-Disposition:.{200}]],'ijo')
				if not kkkkk then 
				    k3=ngx.re.match(k2,[[Content-Disposition:.+Content-Type:]])
				    if not k3 then return return_error(7) end 
				    if not ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"; filename=""Content-Type:]],'ijo') and not  ngx.re.match(k2,[[Content-Disposition: form-data; name=".+"; filename=".+"Content-Type:]],'ijo') then 
				        is_type='恶意上传'
            	        return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP5')
            	    end 
				else
				    k3=ngx.re.match(kkkkk[0],[[Content-Disposition:.+Content-Type:]])
				    if not k3 then 
				        -- is_type='恶意上传'
				        -- return lan_ip('disable_upload_ext','上传的文件名非法,文件名过长,或者为空') 
				        return false
				    end 
					if not ngx.re.match(k3[0],[[Content-Disposition: form-data; name=".+"; filename=""Content-Type:]],'ijo') and not  ngx.re.match(k3[0],[[Content-Disposition: form-data; name=".+"; filename=".+"Content-Type:]],'ijo') then
					     is_type='恶意上传'
            	        return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP7')
            	    end
				end
				k3=k3[0]
        	    if not ngx.re.match(k3,[[filename=""Content-Type]],'ijo') and  not ngx.re.match(k3,[[filename=".+"Content-Type]],'ijo') then 
        			return_error(8)
        	    else
        	    	check_filename=ngx.re.match(k3,[[filename="(.+)"Content-Type]],'ijo')
        	        if check_filename then 
        	            if check_filename[1] then
        	                --return return_message(200,check_filename) 
        	                if ngx.re.match(check_filename[1],'name=','ijo') then return return_error(9) end 
        	                if ngx.re.match(check_filename[1],'php','ijo') then return return_error(10) end 
        	                if ngx.re.match(check_filename[1],'jsp','ijo') then return return_error(11) end 
        	            end 
        	        end
        	        if #k3 >=200 then 
        	           is_type='文件名过长'
                       write_log('post','上传的文件名太长了,被系统拦截')
                       return return_message(200,k3)
        	        end
        	        k3 = string.lower(k3)
        	        if site_config[server_name] ==nil then return false end 
                	disa=site_config[server_name]['disable_upload_ext']
                	if is_ngx_match(disa,k3,'post') then
                	    is_type='恶意上传'
                		lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP1'..' >> '..k3)
                		return true
                	end
        	    end
            end 
        end 
	 end
end



-- 替换函数
function gusb_string(table)
	ret={"-","]","@","#","&","_","{","}"}
	ret2={}
	if arrlen(table)==0 then return table end 
	for _,v in pairs(table) do
		for _,v2 in pairs(ret) do 
			if ngx.re.find(v[0],v2) then 
				v[0]=ngx.re.gsub(v[0],v2,'baota')
			end
		end
		v[0]=string.gsub(v[0],'%[','baota')
		v[0]=string.gsub(v[0],'%(','baota')
		v[0]=string.gsub(v[0],'%)','baota')
		v[0]=string.gsub(v[0],'%+','baota')
		v[0]=string.gsub(v[0],'%$','baota')
		v[0]=string.gsub(v[0],'%?','baota')
	end
	return table
end 

function return_post_data2()
	if method ~= "POST" then return false end
	content_length=tonumber(request_header['content-length'])
	if not content_length then return false end
	local boundary = get_boundary()
	if boundary then
		ngx.req.read_body()
		local data = ngx.req.get_body_data()
		if not data then 
		   data=ngx.req.get_body_file()
			if data==nil then return false end
            data=read_file_body(data) 
		end
		if not data then return false end
		local tmp2 = ngx.re.gmatch(data,[[Content-Disposition.+filename=]],'ijo')
		ret={}
		while true do
		    local m, err = tmp2()
	      	if m then 
	      		table.insert(ret,m)
	      	else
	      		break
	      	end 
	    end
	    ret=gusb_string(ret)
	    if arrlen(ret)>=1 then  
		    for _,v in pairs(ret) do 
				if not ngx.re.match(v[0],'ContentbaotaDisposition: formbaotadata; name=".+"; filename=') and not ngx.re.match(v[0],'ContentbaotaDisposition: formbaotadata; name=”.+”; filename=') then 
				--if not string.find(v[0],'(%w+):%s(%w+);%s(%w+)=\"(%w+)\";%s(%w+)=') and not string.find(v[0],'(%w+):%s(%w+);%s(%w+)=”(%w+)”;%s(%w+)=') then
					return_error(12)
				end
		    end
	    end
	    if arrlen(ret)==1 then 
	    	return 1 
	    else
	    	return 2 
	    end
	end
	return 3
end


function data_in_php(data)
	if not data then
		return false
	else
		if ngx.re.find(data,[[<\?php]],'ijo') then
		    is_type='webshell防御'
		    error_rule="非法上传php文件被系统拦截"
		    write_log('post','regular')
			return_html(config['post']['status'],cookie_html)
			return true
		else
			return false
		end
	end
end


function cookie()
	if not config['cookie']['open'] or not is_site_config('cookie') then return false end
	if not request_header['cookie'] then return false end
    if type(request_header['cookie']) ~= "string" then return false end
	request_cookie = string.lower(request_header['cookie'])
	if is_ngx_match(cookie_rules,request_cookie,'cookie') then
		write_log('cookie','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end

function de_dict2(l_key,l_data)
	if type(l_data) ~= "table" then return l_data end
	if arrlen(l_data) == 0 then return l_data end
	if not l_data then return false end
	local r_data = {}
	if arrlen(l_data) >= 100 then 
	    is_type='GET参数'
		lan_ip('args','非法请求')
		return true
	end
	for li,lv in pairs(l_data)
	do
		r_data[l_key..tostring(li)] = lv
	end
	return r_data
end

function libinjection_args(requires_data)
	if type(requires_data)~='table' then return false end 
	for k,v in pairs(requires_data) do
		if type(v)=='string' then
			is_body_intercept(v)
		    if config['get_is_sql'] and  is_site_config('get_is_sql') then 
    			local issqli, fingerprint = libinjection.sqli(tostring(ReadFileHelper4(v)))
    			if issqli then 
    			    is_type='SQL注入'
    				error_rule = '语义分析分析出sql注入' .. ' >> ' .. tostring(k)..'='..tostring(v)
    				return true 
    			end
    		end
    		if config['get_is_xss']  then 
    			local isxss = libinjection.xss(tostring(v))
    			if isxss then 
    			    is_type='XSS防御'
    				error_rule = '语义分析分析出xss跨站攻击' .. ' >> ' ..tostring(k)..'='..tostring(v)
    				return true 
    			end
    		end
		end
	end 
	return false
end

function args_urlencoded(request_args)
	if is_ngx_match(args_rules,request_args,'args') then
		write_log('args','regular')
		return_html(config['get']['status'],get_html)
	end 
	if libinjection_args(request_args) then
		ngx.shared.btwaf_data:set(ip..'args','1',360)
		write_log('args','regular')
		return_html(config['get']['status'],get_html)
	end
end

function count_sieze(data)
    count=0
	for k,v in pairs(data) 
	do
	    count=count+1
	end 
	return count
end 

function args()
	if not config['get']['open'] or not is_site_config('get') then return false end	
	--if method == "POST" then return false end
	local list_data = nil
	rd_data={}
	if type(uri_request_args)=='table' then
		for k,v in pairs(uri_request_args)
		do
			if type(v)=='table' then
				table.insert(rd_data,de_dict2(k,v))
			end
		end
	end
	if rd_data then
		if arrlen(rd_data)>=1 then 
			for i,v in ipairs(rd_data) do 
				args_urlencoded(v)
				request_args=_process_json_args(v,uri_request_args)
			end
		else
			request_args=_process_json_args(rd_data,uri_request_args)
		end 
	else
		request_args =_process_json_args(uri_request_args)
	end
	if count_sieze(request_args)>=800 then 
	    is_type="GET参数"
		error_rule = '参数太多GET传递的参数数量超过800,拒绝访问,如有误报请点击误报'
		write_log('args','参数太多GET传递的参数数量超过800,拒绝访问,如有误报请点击误报')
	    return_html_data('网站防火墙','您的请求带有不合法参数，已被网站管理员设置拦截','GET传递的参数数量超过800,拒绝访问','点击误报')
	end
	args_urlencoded(request_args)
end

function url()
	if not config['get']['open'] or not is_site_config('get') then return false end
	if is_ngx_match(url_rules,uri,'url') then
		write_log('url','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end



function url_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_path'])
	do
		if ngx_match(uri,rule,"isjo") then
			is_type='站点URL黑名单'
			write_log('path','regular')
			return_html(config['other']['status'],other_html)
			return true
		end
	end
	return false
end

function url_ext()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_ext'])
	do
		if ngx_match(uri,"\\."..rule.."$","isjo") then
			write_log('url_ext','regular')
			return_html(config['other']['status'],other_html)
			return true
		end
	end
	return false
end

function url_rule_ex()
	if site_config[server_name] == nil then return false end
	if method == "POST" and not request_args then
		content_length=tonumber(request_header['content-length'])
		max_len = 640 * 102400000
		request_args = nil
		if content_length < max_len then
			ngx.req.read_body()
			request_args = ngx.req.get_post_args()
		end
	end
	for _,rule in ipairs(site_config[server_name]['url_rule'])
	do
		if ngx_match(uri,rule[1],"isjo") then
			if is_ngx_match(rule[2],uri_request_args,false) then
				write_log('url_rule','regular')
				return_html(config['other']['status'],other_html)
				return true
			end
			
			if method == "POST" and request_args ~= nil then 
				if is_ngx_match(rule[2],request_args,'post') then
					write_log('post','regular')
					return_html(config['other']['status'],other_html)
					return true
				end
			end
		end
	end
	return false
end

function url_tell()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['url_tell'])
	do
		if ngx_match(uri,rule[1],"isjo") then
			if uri_request_args[rule[2]] ~= rule[3] then
				is_type="受保护的URL"
				write_log('url_tell','regular')
				return_html(config['other']['status'],other_html)
				return true
			end
		end
	end
	return false
end

function continue_key(key)
    if method~='POST' then return true end  
	key = tostring(key)
	if string.len(key) > 64 then return false end;
	local keys = {"content","contents","body","msg","file","files","img","newcontent","message","subject","kw","srchtxt",""}
	for _,k in ipairs(keys)
	do
		if k == key then return false end;
	end
	return true;
end

function is_ngx_match(rules,sbody,rule_name)
	if rules == nil or sbody == nil then return false end
	if type(sbody) == "string" then
		sbody = {sbody}
	end
	
	if type(rules) == "string" then
		rules = {rules}
	end

	for k,body in pairs(sbody)
    do  
		if continue_key(k) then
			for i,rule in ipairs(rules)
			do
				if site_config[server_name] and rule_name then
					local n = i - 1
					for _,j in ipairs(site_config[server_name]['disable_rule'][rule_name])
					do
						if n == j then
							rule = ""
						end
					end
				end
				if body and rule ~="" then
					if type(body) == "string" then
						if ngx_match(ngx.unescape_uri(body),rule,"isjo") then
						    is_type =is_type_return(rule_name,rule)
							error_rule = rule .. ' >> ' .. k .. '=' .. body.. ' >> ' .. body
							return true
						end
					end
					if type(k) == "string" then
						if ngx_match(ngx.unescape_uri(k),rule,"isjo") then
						    is_type =is_type_return(rule_name,rule)
							error_rule = rule .. ' >> ' .. k..' >> '..k
							return true
						end
					end
				end
			end
		end
	end
	return false
end

function get_return_state(rstate,rmsg)
	result = {}
	result['status'] = rstate
	result['msg'] = rmsg
	return result
end

function get_btwaf_drop_ip()
	local data =  ngx.shared.drop_ip:get_keys(0)
	return data
end

function remove_btwaf_drop_ip()
	if not uri_request_args['ip'] or not is_ipaddr(uri_request_args['ip']) then return get_return_state(true,'格式错误') end
	if ngx.shared.btwaf:get(cpath2 .. 'stop_ip') then
		ret=ngx.shared.btwaf:get(cpath2 .. 'stop_ip')
		ip_data=json.decode(ret)
        result=is_chekc_table(ip_data,uri_request_args['ip'])
        os.execute("sleep " .. 0.6)
        ret2=ngx.shared.btwaf:get(cpath2 .. 'stop_ip')
        ip_data2=json.decode(ret2)
        if result == 3 then
	    	for k,v in pairs(ip_data2)
		    do
		        if uri_request_args['ip'] == v['ip'] then 
		            v['time']=0
		        end
		    end
		end
	  	save_ip_on(ip_data2)
	end
	ngx.shared.drop_ip:delete(uri_request_args['ip'])
	--ngx.shared.btwaf_data:set(uri_request_args['ip'] .. 'baimingdna','1',360)
	return get_return_state(true,uri_request_args['ip'] .. '已解封')
end

function clean_btwaf_drop_ip()
	if ngx.shared.btwaf:get(cpath2 .. 'stop_ip') then
        ret2=ngx.shared.btwaf:get(cpath2 .. 'stop_ip')
        ip_data2=json.decode(ret2)
    	for k,v in pairs(ip_data2)
	    do
	            v['time']=0
	    end
	  	save_ip_on(ip_data2)
	  	os.execute("sleep " .. 2)
	end
	local data = get_btwaf_drop_ip()
	for _,value in ipairs(data)
	do
		ngx.shared.drop_ip:delete(value)
	end
	return get_return_state(true,'已解封所有封锁IP')
end

function get_btwaf_captcha_base64()
	local token = ngx.md5(ip..'base64')
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
		if count > config['retry'] then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			local lock_time = (config['retry_time'] * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			ngx.shared.drop_ip:set(ip,retry+1,lock_time)
			lan_ip('cc','防火墙获取验证码接口遭到该IP攻击:  '..cycle..'秒内累计超过'..config['retry']..'次请求,封锁' .. lock_time .. '秒')
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,config['retry_cycle'])
	end
	math.randomseed(tostring(os.time()):reverse():sub(1, 6))
	local n1 = math.random(1,200)
	ngx.shared.btwaf:set(ip..'__captcha',captcha_num2[tostring(n1)],180)
	file_name='/www/server/btwaf/captcha/'..n1..'_'..captcha_num2[tostring(n1)]..'.png'
	data=re_png(file_name)
	return get_return_state(true,ngx.encode_base64(data))
end

function Verification_auth_btwaf()
	local token = ngx.md5(ip..'auth')
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
		if count > config['retry'] then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			local lock_time = (config['retry_time'] * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			ngx.shared.drop_ip:set(ip,retry+1,lock_time)
			lan_ip('cc','防火墙验证码接口遭到该IP攻击:  '..cycle..'秒内累计超过'..config['retry']..'次请求,封锁' .. lock_time .. '秒')
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,config['retry_cycle'])
	end
	
	num2=ngx.shared.btwaf:get(ip..'__captcha')
	if num2 ==nil then  return get_return_state(false,'验证码已经过期') end
	if uri_request_args['captcha'] then
		if num2 ==string.lower(uri_request_args['captcha']) then 
			ngx.shared.btwaf:set(ip..'_is_ok',666,18000)
			return get_return_state(true,'验证成功')
		else
			return get_return_state(false,'验证码错误')
		end 
	end
	return get_return_state(false,'请填写验证码')
end

function min_route()
    if request_uri==nil then return false end 
	uri_check=split(request_uri,'?')
	if not uri_check[1] then return false end 
	if uri_check[1] == '/get_btwaf_captcha_base64' then 
		return_message(200,get_btwaf_captcha_base64())
	end
	if uri_check[1] == '/Verification_auth_btwaf' then 
		return_message(200,Verification_auth_btwaf())
	end

	if ngx.var.remote_addr ~= '127.0.0.1' then return false end
	if uri == '/get_btwaf_drop_ip' then
		return_message(200,get_btwaf_drop_ip())
	elseif uri == '/remove_btwaf_drop_ip' then
		return_message(200,remove_btwaf_drop_ip())
	elseif uri == '/clean_btwaf_drop_ip' then
		return_message(200,clean_btwaf_drop_ip())
	end
end


function return_message(status,msg)
	ngx.header.content_type = "application/json;"
	ngx.status = status
	ngx.say(json.encode(msg))
    ngx.exit(status)
end

function return_html(status,html)
	ngx.header.content_type = "text/html"
    ngx.status = status
    ngx.say(html)
    ngx.exit(status)
end

function get_server_name()
	local c_name = ngx.var.server_name
	local my_name = ngx.shared.btwaf:get(c_name)
	if my_name then return my_name end
	local tmp = read_file_body(cpath .. '/domains.json')
	if not tmp then return c_name end
	local domains = json.decode(tmp)
	for _,v in ipairs(domains)
	do
		for _,d_name in ipairs(v['domains'])
		do
			if c_name == d_name then
				ngx.shared.btwaf:set(c_name,v['name'],3600)
				return v['name']
			end
		end
	end
	return c_name
end

function post_referer()
	if method ~= "POST" then return false end
	if is_ngx_match(referer_local,request_header['Referer'],'post') then
		write_log('post_referer','regular')
		return_html(config['post']['status'],post_html)
		return true
	end
	return false
end

function referer()
	if method ~= "GET" then return false end
	if not config['get']['open'] or not is_site_config('get') then return false end
	if is_ngx_match(referer_local,request_header['Referer'],'args') then
		write_log('get_referer','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end


local function return_zhi()
    return require "zhi"
end 

function ua_whilie(ua)
	ua_list2=return_zhi()
	if ua_list2 ~= nil then
		for _,k in ipairs(ua_list2['continue'])
			do
			if k ~= nil then
				local ua=string.find(tostring(ua),tostring(k))
				if ua ~= nil then
					return true
				end
			end
		end
	end
end

function  host_pachong(ip,id,ua_key)
	if not ip then return 33 end
	if not id then return 33 end
	if not ua_key then return 33 end
	key_id=ngx.shared.btwaf:get(ip..'baidu')
	if key_id == nil then 
		local r,err= resolver:new{
                nameservers = {"8.8.8.8", {"114.114.114.114", 53} },
                retrans = 5,  
                timeout = 2000}
        if not r then return 1888 end
		data11111=r:reverse_query(tostring(ip))
		if not data11111 then 
			return 33
		end
		if type(data11111)~='table' then return 1888 end
		if data11111['errcode'] then return 1888 end 
		if not data11111[1] then return 1888 end 
		if not  data11111[1]['ptrdname'] then return 1888 end  
		types=string.find(string.lower(tostring(data11111[1]['ptrdname'])),string.lower(tostring(ua_key)))
		if types~=nil then 
			ngx.shared.btwaf:set(ip..'baidu',1,10000)
			return 2
		else
			return 33
		end
	else
		return 2
	end	
end

function zhizu_ua_chkec(ua)
	ua_list2=return_zhi()
	if ua_list2 ~= nil then
		for _,k in ipairs(ua_list2['types'])
		do
				if k['ua_key'] ~= nil then
					local fa=string.find(string.lower(tostring(ua)),string.lower(tostring(k['ua_key'])))
					if fa ~= nil then
						return tonumber(k['id'])
					end
				end
		end
	end
end

function fei_zhizu_check(ip)
	ret=ngx.shared.btwaf:get('fei_pachong'..ip)
	if not ret then
		return false
	else
		return true
	end
end

function get_zhizu_json(name)
    if ngx.shared.btwaf_data:get(cpath..name..'reptile') then return ngx.shared.btwaf_data:get(cpath..name..'reptile') end
	data = read_file_body(cpath .. tostring(name) ..'.json')
	if not data then 
		data={}
	end 
	ngx.shared.btwaf_data:set(cpath..name..'reptile',data,10000)
	return data
end

function save_data_on(name,data)
	local extime=18000
	data=json.encode(data)
	ngx.shared.btwaf:set(cpath .. name,data,extime)
	if not ngx.shared.btwaf:get(cpath .. name .. '_lock') then
		ngx.shared.btwaf:set(cpath .. name .. '_lock',1,5) 
		write_file(cpath .. name .. '.json',data)
	end
end

function get_ua_key(id)
	zhizu_list=return_zhi()
	if not zhizu_list then return false end
	for _,k in ipairs(zhizu_list['types'])
	do 	
		if tonumber(id) == tonumber(k['id']) then
			return k['host_key']
		end
	end
end

function zhizu_chekc(name,ip)
	data=get_zhizu_json(name)
	local ok ,zhizhu_list_data = pcall(function()
		return json.decode(data)
	end)
	if not ok then
	    return false
	end
	for _,k in ipairs(zhizhu_list_data)
	do
		if tostring(k) == tostring(ip) then 
			return true
		end
	end
end

function reptile_entrance(ua,ip)
	if not ip then return 1 end
	ua_whilie_check=ua_whilie(ua)
	if  ua_whilie_check then return 4.1 end
	reptile_id=zhizu_ua_chkec(ua)
	if not reptile_id then return 4.2 end
	get_ua_key22=get_ua_key(tonumber(reptile_id))
	if not get_ua_key22 then return 6 end
	if get_ua_key22 == nil then return 6 end 
	if fei_zhizu_check(ip) then return 33 end
	if tonumber(reptile_id) == '3' then 
		if zhizu_chekc(reptile_id,ip) then
			return 2 
		else
			return 33
		end
	end
	if zhizu_chekc(reptile_id,ip) then
		return 2
	else
	    baidu_error_count=ngx.shared.btwaf_data:get(ip..'baidu_error')  
	    if not baidu_error_count then 
		    ret=host_pachong(ip,reptile_id,get_ua_key22)
		    if ret~=2 then 
		       baidu_error_count=ngx.shared.btwaf_data:set(ip..'baidu_error',1,1800) 
		    end
	    elseif baidu_error_count>50 then 
	        return 188
	    else
	        ret=host_pachong(ip,reptile_id,get_ua_key22)
	        if ret~=2 then 
	            ngx.shared.btwaf_data:incr(ip..'baidu_error',1)
		    end
		end
		return ret
	end
end

function X_Forwarded()
	if not config['get']['open'] or not is_site_config('get') then return false end	
	if is_ngx_match(args_rules,request_header['X-forwarded-For'],'args') then
		write_log('args','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end

-- function post_X_Forwarded()
-- 	if not config['post']['open'] or not is_site_config('post') then return false end	
-- 	if method ~= "POST" then return false end
-- 	if is_ngx_match(post_rules,request_header['X-forwarded-For'],'post') then
-- 		write_log('post','regular')
-- 		return_html(config['post']['status'],post_html)
-- 		return true
-- 	end
-- 	return false
-- end

function ReadFileHelper(str)
	 if type(str)~='string' then return str end
	 res = string.gsub(str, "\r", "")
	 res = string.gsub(res, "\n", "")
    return res
end


function ReadFileHelper2(str)
	 if type(str)~='string' then return str end
	 res = string.gsub(str, "-", "")
    return res
end

function ReadFileHelper3(str,data)
	 if type(str)~='string' then return str end
	 res = string.gsub(str,data, "")
    return res
end

function post_check(table,data)
	if type(table)~='table' then return false end 
	for k,v in pairs(table) do
		if type(v)=='string' then 
			if string.find(v,data) then 
				return v 
			end 
		end 
	end 
end


function table_key(tbl, key)
    if tbl == nil then
        return false
    end
    for k, v in pairs(tbl) do
        if k == key then
            return true
        end
    end
    return false
end


local function chsize(char)
	if not char then
		print("not char")
		return 0
	elseif char > 240 then
		return 4
	elseif char > 225 then
		return 3
	elseif char > 192 then
		return 2
	else
		return 1
	end
end

function utf8sub(str, startChar, numChars)
	local startIndex = 1
	while startChar > 1 do
		local char = string.byte(str, startIndex)
		startIndex = startIndex + chsize(char)
		startChar = startChar - 1
	end

	local currentIndex = startIndex

	while numChars > 0 and currentIndex <= #str do
		local char = string.byte(str, currentIndex)
		currentIndex = currentIndex + chsize(char)
		numChars = numChars -1
	end
	return str:sub(startIndex, currentIndex - 1)
end


function is_substitution(data)
    data=ngx.re.sub(data,"\\+",'\\+')
    return data
end

function  post_data_chekc()
	if not config['post']['open'] or not is_site_config('post') then return false end
	content_length=tonumber(request_header['content-length'])
	if not content_length then return false end
	if content_length >108246867 then return false end
	if method =="POST" then
		return_post_data=return_post_data2()
		if not return_post_data then return false end 
		if return_post_data==3 then return false end 
				ngx.req.read_body()
		request_args2=ngx.req.get_body_data()
		if not request_args2 then 
		    request_args2=ngx.req.get_body_file()
			if request_args2==nil then return false end 
		    request_args2=read_file_body(request_args2)
		end
		if not request_args2  then return false end
		if not request_header['content-type'] then return false end
		if type(request_header['content-type']) ~= "string" then 
			if type(request_header['content-type']) ~= "string" then 
				return_error(13)
			end
		end
        local p, err = multipart.new(request_args2, ngx.var.http_content_type)
        if not p then
           return false 
        end
        if not ngx.re.match(ReadFileHelper(p['body']),is_substitution(ReadFileHelper(p['boundary2']))..'--$','ijo') then
           	-- is_type='恶意上传'
           	-- lan_ip('post','http包非法,header头部中Content-Type: multipart/form-data; boundary=存在特殊字符.拦截此文件上传的包不。不允许出现【@#%^&*()=\\/】')
           	return return_message(200,is_substitution(ReadFileHelper(p['boundary2'])))
        end
        site_count=0
        local array = {}
        while true do
           local part_body, name, mime, filename,is_filename = p:parse_part()
           if not is_filename then
              break
           end
            site_count=site_count+1
			if is_filename then 
                filename_data=ngx.re.match(is_filename,'filename.+','ijo')
                if filename_data then
					is_type='webshell防御'
                     if ngx.re.match(filename_data[0],'php','ijo') then return lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP13')  end 
        	        if ngx.re.match(filename_data[0],'jsp','ijo') then return lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP14')  end
					if  config['from_data'] then 
						if not ngx.re.match(is_filename,'^Content-Disposition: form-data; name=".+"; filename=".+"Content-Type:') and not ngx.re.match(is_filename,'^Content-Disposition: form-data; name=".+"; filename=""Content-Type:') then 
							  is_type='恶意上传'
							  							  if not ngx.re.match(is_filename,'^Content-Disposition: form-data; name="filename"$',"ijo") then 
							        return return_error(20)
							  end 
						end
					end
				end
				if(#is_filename)>1000 then 
                    lan_ip('disable_upload_ext','非法上传文件名长度超过1000被系统拦截,并封锁IP15') 
                end 

            end
            if filename ~=nil then 
				is_type='webshell防御'
        	    if ngx.re.match(filename,'php','ijo') then return lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP15')  end 
        	    if ngx.re.match(filename,'jsp','ijo') then return lan_ip('disable_upload_ext','上传非法PHP文件被系统拦截,并且被封锁IP16')  end
				if ngx.re.match(filename,'name=','ijo') then return return_error(15) end 
				if (#filename)>=1000 then
        	        lan_ip('disable_upload_ext','非法上传文件名长度超过1000被系统拦截,并封锁IP15') 
        	    end 
            end
            if name ==nil then 
              if part_body then
                    if #part_body>30 then 
                        array[utf8sub(part_body,1,30)]=part_body
                    else
                        array[part_body]=part_body
                    end 
              end
            else
               if #name >300 then 
                  return_error(16)
               end
               
               if filename ==nil then
                   if table_key(array,name) then
                        for i=1, 1000 do
                            if not table_key(array,name..'_'..i) then 
                                 if #name>30 then 
                                    array[utf8sub(name,1,30)..'_'..i]=part_body 
                                 else
                                     array[name..'_'..i]=part_body 
                                 end 
                                 
                                 break
                            end 
                        end 
                    else
                        if #name >30 then 
                            array[utf8sub(name,1,30)]=part_body
                        else 
                            array[name]=part_body
                        end 
                   end
	               if type(part_body)=='string' then
    					if (#part_body) >=200000 then
    						write_log('post',name..'     参数值长度超过20w已被系统拦截')
    						return_html(config['post']['status'],post_html)
    						return true
    					end
	    			end
                else
                    if type(part_body) =='string' and  part_body ~=nil then 
					    if ngx.re.find(part_body,[[phpinfo\(]],'ijo') or ngx.re.find(part_body,[[\$_SERVER]],'ijo') or ngx.re.find(part_body,[[<\?php]],'ijo') or ngx.re.find(part_body,[[fputs]],'ijo') or ngx.re.find(part_body,[[file_put_contents]],'ijo') or ngx.re.find(part_body,[[file_get_contents]],'ijo') or ngx.re.find(part_body,[[eval\(]],'ijo') or ngx.re.find(part_body,[[\$_POST]],'ijo')  or ngx.re.find(part_body,[[\$_GET]],'ijo') or ngx.re.find(part_body,[[base64_decode\(]],'ijo') or ngx.re.find(part_body,[[\$_REQUEST]],'ijo') or ngx.re.find(part_body,[[assert\(]],'ijo') or ngx.re.find(part_body,[[copy\(]],'ijo') or ngx.re.find(part_body,[[create_function\(]],'ijo') or ngx.re.find(part_body,[[preg_replace\(]],'ijo') or ngx.re.find(part_body,[[preg_filter\(]],'ijo') or ngx.re.find(part_body,[[system\(]],'ijo') or ngx.re.find(part_body,[[header_register_callback\(]],'ijo') or ngx.re.find(part_body,[[curl_init\(]],'ijo') or ngx.re.find(part_body,[[curl_error\(]],'ijo') or ngx.re.find(part_body,[[fopen\(]],'ijo')  or ngx.re.find(part_body,[[stream_context_create\(]],'ijo') or ngx.re.find(part_body,[[fsockopen\(]],'ijo')  then
					        is_type='webshell防御'
                            lan_ip('disable_upload_ext','webshell防御.拦截木马上传,并被封锁IP')
                        end 
                    end 
               end
            end
        end
        if site_count==0 then
        	if  config['from_data'] then 
        		return return_error2('','4') 
        	end
        end
        if count_sieze(array)>=800 then
            is_type='POST参数'
			error_rule = '参数太多POST传递的参数数量超过800,拒绝访问,如有误报请点击误报'
		    write_log('post','参数太多POST传递的参数数量超过800,拒绝访问,如有误报请点击误报')
		    return_html_data('网站防火墙','您的请求带有不合法参数，已被网站管理员设置拦截','网站防火墙提醒您multipart/from-data传递的参数数量超过800,拒绝访问','点击误报')
		end
		if array['_method']  and array['method'] and array['server[REQUEST_METHOD]'] then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击')
		end
		if array['_method']  and array['method'] and array['server[]'] and array['get[]'] then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击,并且被封锁IP')
		end
		if array['_method'] and ngx.re.match(array['_method'],'construct','ijo') then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击,并且被封锁IP')
		end
       post_urlencoded(_process_json_args(array))
	   for i,v in pairs(array) do 
            if ngx.re.match(i,'\\\\$','ijo') then 
                is_type='恶意上传'
                return lan_ip('disable_upload_ext','非法上传请求已被系统拦截,并且被封锁IP11') 
            end 
        end 
	end
end

function is_chekc_table(data,strings)
	if type(data) ~= 'table' then return 1 end 
	if not data then return 1 end
	data=chekc_ip_timeout(data)
	for k,v in pairs(data)
    do
        if strings ==v['ip'] then
            return 3
        end
    end
    return 2
end

function chekc_ip_timeout(ip_data)
	resutl=false
	local ret_time=os.time()-180
	for k,v in pairs(ip_data)
	do
		if (v['time']+v['timeout'])<ret_time then
			table.remove(ip_data,k)
			result=true
		end
	end
	if result then
		local extime=18000
		name='stop_ip'
		data=json.encode(ip_data)
		ngx.shared.btwaf:set(cpath2 .. name,data,extime)
		locak_file=read_file_body(cpath2 .. 'stop_ip2.lock')
		if not locak_file then
				write_file(cpath2 .. 'stop_ip2.lock','1')
		end
	end
	return ip_data
end

function insert_ip_list(ip,time,timeout,server_name)
		if time<300 then return false end
        if not ngx.shared.btwaf:get(cpath2 .. 'stop_ip') then
            read_dat=read_file_body(cpath2..'stop_ip.json')
            if not read_dat then 
                write_file(cpath2..'stop_ip.json','[]')
                read_dat=read_file_body(cpath2..'stop_ip.json')
            end 
            ip_data=json.decode(read_dat)
            if not ip_data then return false end
     		result=is_chekc_table(ip_data,ip)
     		if result ==1 then 
     			local myAlldataList={}
                local testData2={timeout=timeout,ip=ip,time=time,site=server_name}
                ip_data={}
                table.insert(ip_data,testData2)
                save_ip_on(ip_data)
     		elseif result==2 then 
     			local myAlldataList={}
                local testData2={timeout=timeout,ip=ip,time=time,site=server_name}
                table.insert(ip_data,testData2)
                save_ip_on(ip_data)
           	elseif result ==3 then
            	for k,v in pairs(ip_data)
			    do
			        if ip ==v['ip'] then 
			            v['time']=time
			            v['timeout']=timeout
			        end
				end
			    save_ip_on(ip_data)
     		end
        else
        	ret=ngx.shared.btwaf:get(cpath2 .. 'stop_ip')
        	ip_data=json.decode(ret)
        	result=is_chekc_table(ip_data,ip)
        	if result ==1 then 
         			local myAlldataList={}
	                local testData2={timeout=timeout,ip=ip,time=time,site=server_name}
	                ip_data={}
	                table.insert(ip_data,testData2)
	                save_ip_on(ip_data)
        	elseif  result==2 then 
         			local myAlldataList={}
	                local testData2={timeout=timeout,ip=ip,time=time,site=server_name}
	                table.insert(ip_data,testData2)
	                save_ip_on(ip_data)
	        elseif result == 3 then
	            	for k,v in pairs(ip_data)
				    do
				        if ip ==v['ip'] then 
				            v['time']=time
				        end
				    end
				  	save_ip_on(ip_data)
         	end
		end	
end

function save_ip_on(data)
	locak_file=read_file_body(cpath2 .. 'stop_ip.lock')
	if not locak_file then
			write_file(cpath2 .. 'stop_ip.lock','1')
	end
	name='stop_ip'
	local extime=18000
	data=json.encode(data)
	ngx.shared.btwaf:set(cpath2 .. name,data,extime)
	if not ngx.shared.btwaf:get(cpath2 .. name .. '_lock') then
		ngx.shared.btwaf:set(cpath2 .. name .. '_lock',1,0.5)
		write_file(cpath2 .. name .. '.json',data)
	end
end

function cc_uri_white()
	if cc_increase_static() then return true end
	if is_ngx_match(cc_uri_white_rules,uri,false) then
		return true
	end
	if site_config[server_name] ~= nil then
		if is_ngx_match(site_config[server_name]['cc_uri_white'],uri,false) then
			return true
		end
	end
	return false
end

function cc_increase_static()
	local keys = {"css","js","png","gif","ico","jpg","jpeg","bmp","flush","swf","pdf","rar","zip","doc","docx","xlsx"}
	for _,k in ipairs(keys)
	do
		local aa="/?.*\\."..k.."$"
		if ngx_match(uri,aa,"isjo") then
			return true
		end
	end
	return false
end

function set_inser_cc()
	if not site_config[server_name] then return false end 
	if not site_config[server_name]['cc'] then return false end
	cc_automatic=false
	cc_time=nil
	cc_retry_cycle=nil
	if site_config[server_name]['cc_automatic'] or config['cc_automatic'] then cc_automatic=true end
	if config['cc_retry_cycle'] then 
	    cc_retry_cycle=config['cc_retry_cycle']
	    cc_time=config['cc_time']*5
	end
	if site_config[server_name]['cc_retry_cycle'] then 
	    cc_retry_cycle=site_config[server_name]['cc_retry_cycle']
	    cc_time=site_config[server_name]['cc_time']*5
	end
	if cc_automatic then
		if cc_time == nil then return false end
		if cc_retry_cycle==nil then return false end
		if not ngx.shared.btwaf:get('cc_automatic'..server_name) then
			ngx.shared.btwaf:set('cc_automatic'..server_name,1,cc_time)
		else
			ret22222=ngx.shared.btwaf:get('cc_automatic'..server_name)
			if (tonumber(ret22222)/2)>tonumber(cc_retry_cycle) then
			    if site_config[server_name] then 
    				site_config[server_name]['cc']['increase']=true
    				site_config[server_name]['cc']['cc_increase_type']='js'
				    cc_increase()
			    else 
			        return false
			    end
			else
			    ngx.shared.btwaf:incr('cc_automatic'..server_name,1)
			end
			
		end
	end
end

function get_body_character_string()
   local char_string=config['uri_find']
   if not char_string then return false end
   if arrlen(char_string) ==0 then return false end
   if arrlen(char_string) >=1 then return char_string end
end

function url_find(uri)
	local get_body=get_body_character_string()
	if get_body then
		for __,v in pairs(get_body)
		do
			if string.find(ngx.unescape_uri(request_uri),v) then
				ngx.exit(444)
			end
		end
	end
end

function get_config_ua_white()
   local char_string=config['ua_white']
   if not char_string then return false end
   if arrlen(char_string) ==0 then return false end
   if arrlen(char_string) >=1 then return char_string end
end

function get_config_ua_black()
   local char_string=config['ua_black']
   if not char_string then return false end
   if arrlen(char_string) ==0 then return false end
   if arrlen(char_string) >=1 then return char_string end
end

function ua_white()
	local ua=ngx.req.get_headers(20000)['user-agent']
	if not ua then return false end
	if type(ua) ~='string' then ngx.exit(200) end 
	local get_ua_list=get_config_ua_white()
	if arrlen(get_ua_list)==0 then return false end
	if get_ua_list then
		for __,v in pairs(get_ua_list)
		do
			if ngx.re.match(ua,v,'ijo') then
				return true
			end
		end
	end
	return false
end

function ua_black()
	local ua=ngx.req.get_headers(20000)['user-agent']
	if not ua then return false end
	if type(ua) ~='string' then ngx.exit(200) end 
	local get_ua_list=get_config_ua_black()
	if arrlen(get_ua_list)==0 then return false end
	if get_ua_list then
		for __,v in pairs(get_ua_list)
		do
			if ngx.re.match(ua,v,'ijo') then
			    is_type='UA黑名单'
				lan_ip('user_agent','UA 黑名单已禁止IP')
			end
		end
	end
	return false
end

function maccms()
	if method == "POST" then 
		if not uri_request_args['m'] then return false end 
		data = ngx.req.get_post_args()
		if data == nil then return false end 
		if not data['wd'] then return false end 
		if uri_request_args['m']=='vod-search' then 
			if data['wd'] then 
				if (#data['wd'])>2000 then 
					write_log('post','拦截苹果CMS RCE,并被封锁IP')
					return_html(config['post']['status'],post_html)
				end
			end
		end
	end
end

function ThinkPHP_RCE5_0_23()
	if method == "POST" then
		ngx.req.read_body()
		data = ngx.req.get_post_args()
		if data==nil then return false end 
		if data['_method']  and data['method'] and data['server[REQUEST_METHOD]'] then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击')
		end
		if data['_method']  and data['method'] and data['server[]'] and data['get[]'] then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击,并且被封锁IP')
		end
		if data['_method'] and ngx.re.match(data['_method'],'construct','ijo') then
		    is_type='ThinkPHP攻击'
			lan_ip('post','拦截ThinkPHP 5.x RCE 攻击,并且被封锁IP')
		end
	end
	return false
end

function ThinkPHP_3_log()
	if string.find(uri,'^/Application/.+log$') or string.find(uri,'^/Application/.+php$') or string.find(uri,'^/application/.+log$') or string.find(uri,'^/application/.+php$') then 
	    is_type='ThinkPHP攻击'
		lan_ip('args','拦截ThinkPHP 3.x 获取敏感信息操作,并且被封锁IP')
	end
	if string.find(uri,'^/Runtime/.+log$') or string.find(uri,'^/Runtime/.+php$')  or string.find(uri,'^/runtime/.+php$') or string.find(uri,'^/runtime/.+log$')then 
	    is_type='ThinkPHP攻击'
		lan_ip('args','拦截ThinkPHP 3.x 获取敏感信息操作,并且被封锁IP')
	end
	return false
end


function error_transfer_encoding()
	if request_header['transfer-encoding'] == nil then return false end 
	if request_header['transfer-encoding'] then
	    is_type='GET参数'
		lan_ip('args','拦截 Transfer-Encoding 块请求,并且被封锁IP')
		return true
	else
		return false
	end
end

function get_json_data(name)
	if  ngx.shared.btwaf:get(cpath .. name) then return ngx.shared.btwaf:get(cpath .. name) end
	data = read_file_body(cpath .. name ..'.json')
	if not data then 
		data={}
	end
	ngx.shared.btwaf:set(cpath .. name,data,180)
	return data
end



function url_white_chekc()
   local char_string=config['url_white_chekc']
   if not char_string then return false end
   if arrlen(char_string) ==0 then return false end
   if arrlen(char_string) >=1 then return char_string end
end

function url_white_chekc_data()
	local get_body=url_white_chekc()
	if request_uri==nil then return false end 
	url_data=split(request_uri,'?')
	if not url_data[1] then return false end
	if get_body and url_data[1] then
		for __,v in pairs(get_body)
		do
			if string.find(url_data[1],v) then 
				return true
			end
		end
	end
	return false
end

function string.split(str, delimiter)
	if str==nil or str=='' or delimiter==nil then
		return nil
	end
    local result = {}
    for match in (str..delimiter):gmatch("(.-)"..delimiter) do
        table.insert(result, match)
    end
    return result
end

function string.trim (s) return (string.gsub(s, "^%s*(.-)%s*$", "%1")) end
 
function getUAField(t)
	local separator=';'
	local tab={}
	local android=string.find(t,"Android")
        local iphone=string.find(t,"Mac")
	local windows=string.find(t,"Windows")
 	if android  then
		tab["platform"]="android"
    		tab["ismobiledevice"]="true"
		local startIndex =string.find(t,"Build")
		if startIndex then
			local res=string.sub(t,0,startIndex-1)
			local rtable=string.split(res,separator)
			local devicename=string.trim(rtable[#rtable])
			local name=string.find(t,"XiaoMi")
			if name then
				local name1 = string.sub(t,name,name+6)
				tab["number"]=name
				if devicename~=nil then
					tab["devicename"]=name1 .. "/" .. devicename
				end
			else
				if devicename~=nil then
					tab["devicename"]=devicename
				end
			end
		end
 
		local osvTable=string.split(string.sub(t,android) ,separator)
		if osvTable then
			local osvTab=string.split(osvTable[1] ,' ')
			tab["os_version"]=string.trim(osvTab[#osvTab])
		end
	end
 
	if iphone then
		local ipho = string.find(t,"iPhone")
		local mac = string.find(t,"Macintosh")
		if ipho then
			tab["platform"]="iOS"
			tab["devicename"]="iphone"
			tab["number"]=ipho	
			tab["ismobiledevice"]="true"
 			local vs=string.find(t,"CPU")	
			if vs then
			    local osvTable=string.sub(t,vs)
			    local osvTable1 = string.split(osvTable,' ')
		            local osversion = string.trim(osvTable1[4])
			    tab["os_version"]=osversion
		        end	
		end
		if mac then
			tab["platform"]="Mac"
			tab["number"]=mac
			tab["devicename"]="PC"
			tab["ismobiledevice"]="flase"
			local osvers = string.sub(t,mac)
			local osversi= string.split(osvers,separator)
			if osversi then
				local osvTab = string.split(osversi[2],' ')
				table["os_version"]=string.trim(osvTab[5])
			end
		end
	end
    if windows  then
		tab["platform"]="Windows"
		tab["ismobiledevice"]="flase"
		local osvTable=string.split(string.sub(t,windows) ,separator)
		if osvTable then
			local osvTab=string.split(osvTable[1] ,' ')
			tab["os_version"]=string.trim(osvTab[#osvTab])
			tab["devicename"]="PC"
		end
	end
	if  next(tab)  == nil then
		tab["platform"]=""
		tab["devicename"]=""
		tab["os_version"]=""
		tab["number"]=""
		tab["ismobiledevice"]=""
	end
 
	return tab
 
end

function send_Verification()
	local token = ngx.md5(ip)
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
		if count > config['retry'] then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			local lock_time = (config['retry_time'] * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			ngx.shared.drop_ip:set(ip,retry+1,lock_time)
			lan_ip('cc','人机验证页面遭到该IP攻击:  '..config['retry_cycle']..'秒内累计超过'..config['retry']..'次请求,封锁' .. lock_time .. '秒')
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,config['retry_cycle'])
	end

	if not request_header['user-agent'] then request_header['user-agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64)' end
	ua_type=getUAField(request_header['user-agent'])
	if ua_type["platform"] == "android" or ua_type["platform"]=="iOS" then 
		local jsbody= string.format([[
<html>
	<head>
		<title>宝塔防火墙</title>
		<style>
			body{font-family:Tahoma,Verdana,Arial,sans-serif;}.head_title{margin-top:0;font-family:"微软雅黑";font-size:50px;font-weight:lighter;}p{font-family:"微软雅黑";font-size:16px;font-weight:lighter;color:#666666;}.btn{width:90vw;height:11.5vw;line-height:11.5vw;text-align:center;font-size:4vw;background:#20a53a;box-shadow:inset 0 1px 2px #30ad42;color:#fff;text-shadow:#00851a 0 -1px 0;font-family:"微软雅黑";border:0;cursor:pointer;transition:all 500ms;margin-top:3vw;}.btn:hover{color:#fff;background-color:#008e1c;border-color:#398439;}.inp_captcha{float:left;padding:10px;width:58vw;box-sizing:border-box;padding-left:2vw;height:12vw;font-size:5vw;border:2px solid #c0c0c0;outline:none;border-right:0;}.inp_captcha:focus{border:2px solid #20a53a;border-right:0;padding-left:3vw;}.yzm{float:left;width:30vw;height:12vw;line-height:12vw;font-size:4vw;color:#333;border-radius:2px;border:2px solid #c0c0c0;box-sizing:border-box;}.form{margin:0 auto;overflow:hidden;margin-top:3.5vw;}.captcha-box{margin-top:20vw;padding:0 5vw;}#errmsg{font-size: 4vw;}
		</style>
	</head>
	<body>
		<script>
			if (window != top) {
				location.href = location.href
			}
		</script>
		<div align="center" class="captcha-box">
			<div class="tit">
				<img src="data:image/jpg;base64,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" alt="" style="width:30vw;padding-bottom:10px"/>
			</div>
			<p style="font-weight: 400;font-size: 4.8vw;margin-bottom:1.5vw ">此为人机校验，请输入验证码继续访问</p>
			<p style="margin:0"><font color="red" id="errmsg"></font></p>
			<form class="form" action="#" onsubmit="return false" method="POST">
				<input id="value" class="inp_captcha" name="captcha" type="text" />
				<img class="yzm" id="yzm" onclick="showCaptcha()" alt="验证码图片">
				<button type="submit" class="btn" onclick="mfwaf_auth()" type="button">提交</button>
			</form>
		</div>
		<script>
			document.onkeydown=function(e){var theEvent=window.event||e;var code=theEvent.keyCode||theEvent.which||theEvent.charCode;if(code==13){var value=document.getElementById("value").value;var c="/Verification_auth_btwaf?captcha="+value;mfajax2("GET",c)}};function showCaptcha(){var t=(new Date()).valueOf();var b="/get_btwaf_captcha_base64?captcha="+t;mfajax("GET",b)}showCaptcha();function mfajax(a,b,c){var xmlHttp=new XMLHttpRequest();xmlHttp.onreadystatechange=function(){if(xmlHttp.readyState==4&&xmlHttp.status==200){var data=JSON.parse(xmlHttp.responseText);if(data.status==true){yzm.src="data:image/png;base64,"+data.msg}else{if(data.status){location.href=location.href}else{errmsg.innerHTML="验证码输入错误，请重新输入"}}}else{if(xmlHttp.readyState==4&&xmlHttp.status==404){if(a=="GET"){errmsg.innerHTML="无法获取验证码"}else{errmsg.innerHTML="此IP可能已经被屏蔽，请明天或稍后再试"}}}};xmlHttp.open(a,b,true);xmlHttp.send(c)}function mfajax2(a,b,c){var xmlHttp=new XMLHttpRequest();xmlHttp.onreadystatechange=function(){if(xmlHttp.readyState==4&&xmlHttp.status==200){var data=JSON.parse(xmlHttp.responseText);if(data.status==true){location.href=location.href}else{if(data.status){location.href=location.href}else{errmsg.innerHTML="验证码输入错误，请重新输入"}}}else{if(xmlHttp.readyState==4&&xmlHttp.status==404){if(a=="GET"){errmsg.innerHTML="无法获取验证码"}else{errmsg.innerHTML="此IP可能已经被屏蔽，请明天或稍后再试"}}}};xmlHttp.open(a,b,true);xmlHttp.send(c)}function mfwaf_auth(){var value=document.getElementById("value").value;var c="/Verification_auth_btwaf?captcha="+value;mfajax2("GET",c)};
		</script>
	</body>
	</html>
	]])
		ngx.header.content_type = "text/html;charset=utf8"
		ngx.say(jsbody)
		ngx.exit(200)
	else
		local jsbody22 = string.format([[
	<html><head><title>宝塔防火墙</title>
	<style>body{font-family:Tahoma,Verdana,Arial,sans-serif}.head_title{margin-top:0;font-family:"微软雅黑";font-size:50px;font-weight:lighter}p{font-family:"微软雅黑";font-size:16px;font-weight:lighter;color:#666}.btn{float:left;width:63px;height:40px;background:#20a53a;box-shadow:inset 0 1px 2px #30ad42;color:#fff;text-shadow:#00851a 0 -1px 0;font-family:"微软雅黑";font-size:16px;border:0;cursor:pointer;outline:0;border-top-right-radius:2px;border-bottom-right-radius:2px;transition:all 500ms}.btn:hover{color:#fff;background-color:#008e1c;border-color:#398439}.inp_captcha{float:left;margin-left:10px;padding:10px;width:200px;height:40px;font-size:20px;border-top-left-radius:2px;border-bottom-left-radius:2px;border:1px solid #c0c0c0;outline:0;border-right:0}.inp_captcha:focus{border:1px solid #20a53a;border-right:0}.yzm{float:left;width:130px;height:40px;border-radius:2px}.form{margin:0 auto;width:415px;height:40px}</style>
	</head><body>
	<script>if (window != top) {location.href = location.href;}</script>
	<div align="center" class="captcha-box" style="margin-top:150px"><div class="tit">
	<img src="data:image/jpg;base64,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" alt="" style="width:130px;padding-bottom:10px"/>
	</div>
	<p style="font-weight: 400;font-size: 17px">此为人机校验，请输入验证码来继续访问 (PS: 如需关闭此功能请在防火墙中关闭增强模式 )：</p><p><font color="red" id="errmsg"></font></p>
	<form class="form" action="#" onsubmit="return false" method="POST"><img class="yzm" id="yzm" onclick="showCaptcha()" alt="验证码图片"><input id="value" class="inp_captcha" name="captcha" type="text" /><button type="submit" class="btn" onclick="mfwaf_auth()" type="button">提交</button></form>
	</div>
	<script>document.onkeydown=function(e){var theEvent=window.event||e;var code=theEvent.keyCode||theEvent.which||theEvent.charCode;if(code==13){var value=document.getElementById("value").value;var c="/Verification_auth_btwaf?captcha="+value;mfajax2("GET",c)}};function showCaptcha(){var t=(new Date()).valueOf();var b="/get_btwaf_captcha_base64?captcha="+t;mfajax("GET",b)}showCaptcha();function mfajax(a,b,c){var xmlHttp=new XMLHttpRequest();xmlHttp.onreadystatechange=function(){if(xmlHttp.readyState==4&&xmlHttp.status==200){var data=JSON.parse(xmlHttp.responseText);if(data.status==true){yzm.src="data:image/png;base64,"+data.msg}else{if(data.status){location.href=location.href}else{errmsg.innerHTML="验证码输入错误，请重新输入"}}}else{if(xmlHttp.readyState==4&&xmlHttp.status==404){if(a=="GET"){errmsg.innerHTML="无法获取验证码"}else{errmsg.innerHTML="此IP可能已经被屏蔽，请明天或稍后再试"}}}};xmlHttp.open(a,b,true);xmlHttp.send(c)}function mfajax2(a,b,c){var xmlHttp=new XMLHttpRequest();xmlHttp.onreadystatechange=function(){if(xmlHttp.readyState==4&&xmlHttp.status==200){var data=JSON.parse(xmlHttp.responseText);if(data.status==true){location.href=location.href}else{if(data.status){location.href=location.href}else{errmsg.innerHTML="验证码输入错误，请重新输入"}}}else{if(xmlHttp.readyState==4&&xmlHttp.status==404){if(a=="GET"){errmsg.innerHTML="无法获取验证码"}else{errmsg.innerHTML="此IP可能已经被屏蔽，请明天或稍后再试"}}}};xmlHttp.open(a,b,true);xmlHttp.send(c)}function mfwaf_auth(){var value=document.getElementById("value").value;var c="/Verification_auth_btwaf?captcha="+value;mfajax2("GET",c)};</script>
	</body></html>
		]])
		ngx.header.content_type = "text/html;charset=utf8"
		ngx.say(jsbody22)
		ngx.exit(200)
	 end

end 

function cc2()
	if not config['cc']['open'] or not site_cc then return false end
	if not site_config[server_name] then return false end
	if not site_config[server_name]['cc']['increase'] then return false end
	if site_config[server_name]['cc']['cc_increase_type']=='js' then return false end
	if ngx_match(uri,"\\.(css|js|png|gif|ico|jpg|jpeg|bmp|flush|swf|pdf|rar|zip|doc|docx|xlsx|ts)$","isjo") then return false end
	sv,_ = ngx.shared.btwaf:get(ip..'_is_ok')
	if sv == 666 then return false end
	send_Verification()
end


function cc3()
	if not config['cc']['open'] or not site_cc then return false end
	if ngx.re.find(uri,'/uc_server/avatar.php') then return false end
	if not site_config[server_name] then return false end
	if not site_config[server_name]['cc']['increase'] then return false end
	if site_config[server_name]['cc']['cc_increase_type']=='code' then 
		cc2()
		
	else 
		cc_increase()
	end
end

function  return_error3(method,msg)
	error_rule = msg
	write_log(method,msg)
end 

function method_type_check(method)
    if not config['method_type'] then 
        return true
    else
        method_type=config['method_type']
    end
    for i,v in ipairs(method_type) do
        if method == v[1] and v[2] then 
            return true 
        end
    end 
    return false 
end 

function header_check(header_data,len_data,header)
    for i,v in pairs(header_data) do
            if header == v[1] then 
                 if tonumber(len_data)>tonumber(v[2]) then return true end 
                 return false
            end
    end 
   	if len_data>20000 then return true end
    return false
end 

function header_len_check(request_header)
	if method=='PROPFIND' or  method=='PROPPATCH' or method=='MKCOL' or method=='CONNECT'  or method=='SRARCH' then return false end
    if not  method_type_check(method) then
    	return_error3(method,'宝塔WAF提醒您不允许您当前的请求类型'..method..'此请求类型已经被禁用。如需开启请在Nginx防火墙-->全局设置-->HTTP请求过滤-->请求类型过滤开启'..method..'请求') 
    	return_html_data('网站防火墙','宝塔WAF提醒您不允许您当前的请求类型','宝塔WAF提醒您不允许您当前的请求类型','Nginx防火墙-->全局设置-->HTTP请求过滤-->请求类型过滤开启'..method..'请求')
    end
    if not request_header then  
    	return_error3(method,'宝塔WAF提醒您header获取失败,可能是头部请求太长,如有误报.请调整nginx的header获取大小')
    	return_html_data('网站防火墙','网站防火墙提醒您header获取失败','网站防火墙提醒您header获取失败','调整nginx的header获取大小')
    end
    if not  config['header_len'] then
        return false
    else
        header_data=config['header_len']
    end 
    for i,v in pairs(request_header) do
      if  header_check(header_data,#v,i) then  
		if i=='cookie' or i=='user-agent' then return false end 
     	return_error3(method,'网站防火墙提醒您header头部参数'..i..'太长，如有误报请在Nginx防火墙--全局设置--HTTP请求过滤--请求头过滤调整'..i..'的长度,如果没有这个'..i..'的选项需要添加建议把长度默认为10000')
      	return_html_data('网站防火墙','网站防火墙提醒您header头部参数'..i..'太长','网站防火墙提醒您header头部参数'..i..'太长','Nginx防火墙-->全局设置-->HTTP请求过滤-->请求头过滤调整'..i..'的长度。如果没有这个'..i..'的选项需要添加建议把长度默认为10000')
      end
    end
end 

function get_server_path()
  local c_name = ngx.var.server_name
  local my_name = ngx.shared.btwaf:get(c_name..'_path')
  if my_name then return my_name end
  local tmp = read_file_body(cpath .. '/domains.json')
  if not tmp then return false end
  local domains = json.decode(tmp)
  for _,v in ipairs(domains)
  do
     for _,d_name in ipairs(v['domains'])
     do
        if c_name == d_name then
           ngx.shared.btwaf:set(c_name..'_path',v['path'],3600)
           return v['path']
        end
     end
  end
  return false
end

function check_find(shell_check,check) 
    for _,k in ipairs(shell_check)
	do
		if tostring(k) == tostring(check) then 
			return true
		end
	end
end 

function webshell_check(request_uri)
    if config['webshell_open'] then
        url_data=split2(request_uri,'?')
        if not url_data then return false end 
        if url_data[1] =='index.php' or url_data[1]=='index.html' then return false end 
        if not get_server_path() then  return false end 
        file_path=get_server_path()..url_data[1]
        if not ngx.re.match(file_path,'php$') then return false end
--         shell_web = json.decode(read_file_body('/www/server/btwaf/webshell.json'))
--         if check_find(shell_web,file_path) then 
--             write_log('args',uri..'检测为webshell,已被系统自动拦截,如为误报,请点击误报.如果想关闭此功能请在防火墙的全局设置中关闭webshell查杀')
-- write_log('args',uri..'检测为webshell,已被系统自动拦截,如为误报,请点击误报.如果想关闭此功能请在防火墙的全局设置中关闭webshell查杀')
--     		return_html_data('网站防火墙webshell主动防御','webshell主动防御','webshell主动防御拦截发现此文件为webshell','请及时删除此文件。</p><p> 2、如有误报、请将【 ^'..url_data[1]..'】加入到【Nginx防火墙】->【全局配置】->【URL白名单中】。</p><p>3、如需关闭webshell查杀。请在【Nginx防火墙】-->【全局设置】-->【webshell查杀】关闭即可</p>')       
--     	end
        if ngx.shared.btwaf_data:get(file_path) then return false end
        shell_code={'assert','eval','$_GET','$_POST','$_REQUEST','base64_decode','file_get_contents','copy'}
        file_data=read_file_body(file_path)
        if file_data==nil then
                ngx.shared.btwaf_data:set(file_path,'1',360)
                return false
        end
        for i,v in pairs(shell_code) do 
            if ngx.re.match(file_data,v) then 
                    if check_find(shell_check,file_path) then 
                        ngx.shared.btwaf_data:set(file_path,'1',360)
                        return false
                    else
                        table.insert(shell_check,file_path)
                        save_data_on('shell_check',shell_check)
                        ngx.shared.btwaf_data:set(file_path,'1',360)
                        return false
                    end
            end
        end
        ngx.shared.btwaf_data:set(file_path,'1',360)
        return false
    end 
end

function  return_html_data(title,t1,li,l2)
	local check_html = [[<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>]]..title..[[</title>
<style>
*{margin:0;padding:0;color:#444}
body{font-size:14px;font-family:"宋体"}
.main{width:600px;margin:10% auto;}
.title{background: #20a53a;color: #fff;font-size: 16px;height: 40px;line-height: 40px;padding-left: 20px;}
.content{background-color:#f3f7f9; height:280px;border:1px dashed #c6d9b6;padding:20px}
.t1{border-bottom: 1px dashed #c6d9b6;color: #ff4000;font-weight: bold; margin: 0 0 20px; padding-bottom: 18px;}
.t2{margin-bottom:8px; font-weight:bold}
ol{margin:0 0 20px 22px;padding:0;}
ol li{line-height:30px}
</style>
</head>

<body>
	<div class="main">
		<div class="title">]]..title..[[</div>
		<div class="content">
			<p class="t1">]]..t1..[[</p>
			<p class="t2">可能原因：</p>
			<ol>
				<li>]]..li..[[</li>
			</ol>
			<p class="t2">如何解决：</p>
			<ol>
				<li>]]..l2..[[</li>
			</ol>
		</div>
	</div>
</body>
<!--8.6.0 -->
</html>
]]
    		ngx.header.content_type = "text/html;charset=utf8"
    		ngx.say(check_html)
    		ngx.exit(200)
end

function php_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_php_path'])
	do
	    url_data=split2(request_uri,'?')
        if not url_data then url_data=request_uri end 
        if not url_data[1] then 
            url_data=request_uri 
        else
            url_data=url_data[1]
        end
		if ngx_match(url_data,rule .. "/?.*\\.php$","isjo") then
		    is_type='目录防护'
			write_log('disable_php_path','Nginx网站防火墙提醒您:当前目录禁止执行PHP文件,如有误报请在Nginx防火墙--站点配置--设置--禁止运行PHP的URL删除当前目录')
			return_html_data('当前目录禁止执行PHP文件','当前目录禁止执行PHP文件','您当前目录设置了禁止访问PHP文件','Nginx防火墙--站点配置--设置--禁止运行PHP的URL删除当前目录')
		end
	end
	return false
end

function is_body_intercept(body)
    if not config['open'] or not is_site_config('open') then return false end
    if not config['body_intercept'] then return false end 
    if arrlen(config['body_intercept'])==0  then return false end
    if config['body_intercept'] then
		for __,v in pairs(config['body_intercept'])
		do
			if ngx.re.match(ngx.unescape_uri(body),v) then
				return_html_data('禁止存在违禁词','禁止存在违禁词','禁止存在违禁词'..'【'..v..'】','禁止存在违禁词'..'【'..v..'】')
			end
		end
	end
end

function ua_whilie2(ua)
	if not ua then return false end 
	ua = string.lower(ua)
    if ngx.re.match(ua,'baiduspider') then return true end 
    if ngx.re.match(ua,'googlebot') then return true end 
    if ngx.re.match(ua,'360spider') then return true end 
    if ngx.re.match(ua,'sogou') then return true end 
    if ngx.re.match(ua,'yahoo') then return true end 
    if ngx.re.match(ua,'bingbot') then return true end 
    if ngx.re.match(ua,'yisouspider') then return true end 
	if ngx.re.match(ua,'haosouspider') then return true end 
	if ngx.re.match(ua,'sosospider') then return true end 
end 

function header_lan(header)
    if not config['is_browser'] then return false end 
    if type(header['connection'])~='string' then return false end 
    if ua_whilie2(request_header['user-agent']) then return false end
    if is_ssl() then return false end
    if header['connection'] =='close' then 
        if method =='GET' then method='args' end 
        if method =='POST' then method ='post' end 
        is_type='非浏览器请求'
        write_log(method,'非浏览器请求已被系统拦截,如想关闭此功能如下操作:Nginx防火墙--全局设置--非浏览器拦截')
	    ngx.exit(200)
    end
end

function is_header_error()
    for k,v in pairs(ngx.req.get_headers(20000)) 
    do
       if k=='cookie'  or k=='host' or k=='origin' or k=='referer' or k=='user-agent' or k=='content-type' then 

            if type(v) ~='string' then
               	error_rule = 'header 头部存在异常'..' >> '..k..' >> '..'不是字符串'
               	is_type='header请求头'
            	write_log('post','header 头部存在异常'..k..'不为字符串')
                local check_html = [[<html><meta charset="utf-8" /><title>header 头部存在异常</title><div>宝塔WAF提醒您,header 请求异常,拒绝访问</div><ml>]]
            		ngx.header.content_type = "textml;charset=utf8"
            		ngx.say(check_html)
            		ngx.exit(200)
            end
        end
    end
end


function check_dir(path)
	local file = io.open(path, "rb")
	if file then file:close() end
	return file ~= nil
end

function create_dir(path)
	os.execute("mkdir -p " .. path)
end

function get_is_type_count(name)
	data = read_file_body(cpath ..'total/' .. tostring(name) ..'.json')
	if not data then return {} end 
	return json.decode(data)
end

function total_count(is_type)
    today = os.date("%Y-%m-%d")
	local path = cpath .. '/total/'
	if not check_dir(path) then create_dir(path) end
    is_type_count=ngx.shared.btwaf:get('is_type_count')
    if  is_type_count==nil then 
        is_type_count=get_is_type_count(today)
    else
        is_type_count =json.decode(is_type_count)
    end
    if is_type =='ThinkPHP攻击' or is_type=='PHP脚本过滤' or is_type=='PHP流协议' then is_type ='PHP函数' end
    if is_type =='GET参数' or is_type=='POST参数' then is_type='参数过滤' end
    if is_type =='文件名过长' or is_type=='http包非法' then is_type ='恶意上传' end
    
    if is_type_count[is_type] ==nil then 
        is_type_count[is_type] =1
    else
        is_type_count[is_type]=is_type_count[is_type]+1
    end
    
    if is_type_count['total'] ==nil then 
        is_type_count['total'] =1
    else
        is_type_count['total']=is_type_count['total']+1
    end
    save_data_on2('total/'..today,is_type_count)
end

function save_data_on2(name,data)
	local extime=1800
	data=json.encode(data)
	ngx.shared.btwaf:set('is_type_count',data,extime)
	if not ngx.shared.btwaf:get(cpath .. name .. '_lock') then
		ngx.shared.btwaf:set(cpath .. name .. '_lock',1,2) 
		write_file(cpath .. name .. '.json',data)
	end
end

function is_check_header()
    is_check_headers=ngx.req.get_headers(2000)
    count=0
	if type(is_check_headers)=='table' then
		for k,v in pairs(is_check_headers)
		do
			if type(v)=='table' then
				for k2,v2 in pairs(v) do 
				   count=count+1 
				end 
			else
			  count=count+1 
			end
		end
	end
	if count>800 then 
	    return lan_ip('post','header字段大于800 被系统拦截') 
	end 
end


function run_btwaf()
	server_name = string.gsub(get_server_name(),'_','.')
	if not config['open'] or not is_site_config('open') then return false end
	error_rule = nil
	request_uri = ngx.var.request_uri
	uri = ngx.unescape_uri(ngx.var.uri)
	method = ngx.req.get_method()
	request_header = ngx.req.get_headers(20000)
	ip = get_client_ip_bylog()
	ipn = arrip(ip)
	ipn2 = ip2long(ip)
	uri_request_args = ngx.req.get_uri_args(100000)
	cycle = config['cc']['cycle']
	endtime = config['cc']['endtime']
	limit = config['cc']['limit']
	retry = config['retry']
	retry_time = config['retry_time']
	retry_cycle = config['retry_cycle']
	min_route()
	site_cc = is_site_config('cc')
	if site_config[server_name] and site_cc then
		cycle = site_config[server_name]['cc']['cycle']
		endtime = site_config[server_name]['cc']['endtime']
		limit = site_config[server_name]['cc']['limit']
	end
	if site_config[server_name] then
		retry = site_config[server_name]['retry']
		retry_time = site_config[server_name]['retry_time']
		retry_cycle = site_config[server_name]['retry_cycle']
	end
	--is_header_error()
	
	--cc_html_dan()
	if ip_white() then return true end
	is_check_header()
	ip_black()
	drop()
	if ua_white() then return true end
	ua_black()
	url_find(request_uri)
	header_len_check(request_header)
	if url_white_chekc_data() then 
		cc()
		args()
		post()
		post_data()
	else
		if url_white() then return true end
		url_black()
		drop_abroad()
		drop_china()
		--webshell_check(request_uri)
		ret=reptile_entrance(request_header['user-agent'],ip)
		if ret == 2 then
			args()
			scan_black()
		    if ThinkPHP_RCE5_0_23() then return true end
			if ThinkPHP_3_log() then return true end
			if error_transfer_encoding() then return true end
			post()
			post_data()
			post_data_chekc()
			if site_config[server_name] then
				--maccms()
				X_Forwarded()
				--post_X_Forwarded()
				php_path()
				url_path()
				url_ext()
				url_rule_ex()
				url_tell()
			end
			return false
		end
		header_lan(request_header)
		user_agent()
		cc()
		set_inser_cc()
		cc3()
		--cc_increase_wuheng()
		url()
	    referer()  
        cookie()
	    args()
		scan_black()
	    if ThinkPHP_RCE5_0_23() then return true end
		if ThinkPHP_3_log() then return true end
		if error_transfer_encoding() then return true end
		post()
		post_data()
		post_data_chekc()
		if site_config[server_name] then
			--maccms()
			X_Forwarded()
			--post_X_Forwarded()
			php_path()
			url_path()
			url_ext()
			url_rule_ex()
			url_tell()
		end
	end
end