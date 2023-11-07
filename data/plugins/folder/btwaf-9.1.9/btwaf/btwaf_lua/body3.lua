--[[
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 梁凯强 <1249648969@qq.com>
#-------------------------------------------------------------------

#----------------------
# WAF防火墙 for nginx  body 过滤
#----------------------
]]--

local cpath = "/www/server/btwaf/"

local function get_body_character_string()
  local char_string=config['body_character_string']
  if not char_string then return false end
  if arrlen(char_string) ==0 then return false end
  if arrlen(char_string) >=1 then return char_string end
end

local function get_site_character_string(waf_site_config)
  if not waf_site_config then return false end
  local char_string=waf_site_config['body_character_string']
  if not char_string then return false end
  if arrlen(char_string) ==0 then return false end
  if arrlen(char_string) >=1 then return char_string end
end
local function split_bylog( str,reps )
	local resultStrList = {}
	string.gsub(str,'[^'..reps..']+',function(w)
		table.insert(resultStrList,w)
	end)
	return resultStrList
end

local function check_type()
  if ngx.header.content_type== nil then return false end
  if string.find(ngx.header.content_type, "text/html") ~= nil or  string.find(ngx.header.content_type, "application/json") ~= nil then
    return true
  end
  return false
end


function split( str,reps )
    if str ==nil then return nil end 
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function(w)
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

local function arrip(ipstr)
	if ipstr == 'unknown' then return {0,0,0,0} end
	if string.find(ipstr,':') then return ipstr end
	iparr = split(ipstr,'.')
	iparr[1] = tonumber(iparr[1])
	iparr[2] = tonumber(iparr[2])
	iparr[3] = tonumber(iparr[3])
	iparr[4] = tonumber(iparr[4])
	return iparr
end

local function compare_ip_block(ips)
	if (string.match(ips,"^%d+%.%d+%.%d+%.%d+$") == nil and string.match(ips,"^[%w:]+$") == nil) or ips == 'unknown'  then return false end
	if not ips then return false end
	if ips=='unknown' then return false end 
	if string.find(ips,':') then return false end
	ips = arrip(ips)
	if not is_max(ips,arrip("127.0.0.255")) then return false end
	if not is_min(ips,arrip("127.0.0.1")) then return false end
	return true
end

local function body_get_client_ip(request_header)
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

local function write_to_file(logstr)
	local filename = config["logs_path"] .. '/' .. server_name .. '_' .. ngx.today() .. '.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	fp:write(logstr)
	fp:flush()
	fp:close()
	return true
end

local function write_log(name,rule,ip,http_user_agent)
	local count,_ = ngx.shared.drop_sum:get(ip..today)
	if count then
		ngx.shared.drop_sum:incr(ip..today,1)
	else
		ngx.shared.drop_sum:set(ip..today,1,retry_cycle)
	end
	local method = ngx.req.get_method()
	local logtmp = {ngx.localtime(),ip,method,ngx.var.request_uri,http_user_agent,name,rule,"","cc"}
	local logstr = json.encode(logtmp) .. "\n"
	local count,_ = ngx.shared.drop_sum:get(ip..today)	
	if name =='cc' then
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
        ngx.shared.btwaf_data:delete(ip)
	end
	write_to_file(logstr)
end


local function write_drop_ip(ip,is_drop,drop_time,name,http_user_agent)
	local filename = cpath .. 'drop_ip.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end

	local logtmp = {os.time(),ip,server_name,ngx.var.request_uri,drop_time,is_drop,ngx.req.get_method(),http_user_agent,name,rule,""}

	local logstr = json.encode(logtmp) .. "\n"
	fp:write(logstr)
	fp:flush()
	fp:close()
	return true
end



local function get_html(ip,user_agent,server_name,today)
    local token = ngx.md5(ip..user_agent.."browser"..server_name..today)
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
	    retry=5
	    if config['retry']>5 then 
	        retry=config['retry']
	    end 
		if count > retry then
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
			bt_ip_filter(ip,lock_time)
			is_type='cc'
			ngx.shared.btwaf:delete(token)
			write_log('cc','浏览器验证当前IP 验证时间为: '..config['retry_cycle']..'秒 累计验证失败'..config['retry']..'次,被防火墙封锁' .. lock_time .. '秒',ip,user_agent)
			write_drop_ip(ip,'cc',lock_time,'浏览器验证当前IP 验证时间为: '..config['retry_cycle']..'秒 累计验证失败'..config['retry']..'次,被防火墙封锁' .. lock_time .. '秒',user_agent)
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,config['retry_cycle'])
	end
    local jsbody= string.format([[
        <!DOCTYPE html>
<html>
        <script src="/Rxizm32rm3CPpyyW_fingerprint2daasdsaaa.js?id=%s%s"></script>
        <script>
        var options={preprocessor:null,audio:{timeout:1000,excludeIOS11:true},fonts:{swfContainerId:'fingerprintjs2',swfPath:'flash/compiled/FontList.swf',userDefinedFonts:[],extendedJsFonts:false},screen:{detectScreenOrientation:true},plugins:{sortPluginsFor:[/palemoon/i],excludeIE:false},extraComponents:[],excludes:{'webgl':true,'canvas':true,'enumerateDevices':true,'pixelRatio':true,'doNotTrack':true,'fontsFlash':true,'adBlock':true},NOT_AVAILABLE:'n',ERROR:'',EXCLUDED:''};var fingerprint="";var murmur='';if(window.requestIdleCallback){requestIdleCallback(function(){Fingerprint2.get(options,function(components){var values=components.map(function(component){return component.value});murmur=Fingerprint2.x64hash128(values.join(''),31);sendWafValida()})})}else{setTimeout(function(){Fingerprint2.get(options,function(components){var values=components.map(function(component){return component.value});murmur=Fingerprint2.x64hash128(values.join(''),31);sendWafValida()})},500)};function sendWafValida(){var key='%s',value='%s',newWord='',newVal='';for(var i=0;i<murmur.length;i++){var _mur=String.fromCharCode(murmur.charAt(i).charCodeAt()-1);newWord+=_mur}for(var j=0;j<value.length;j++){var _val=String.fromCharCode(value.charAt(j).charCodeAt()+1);newVal+=_val};var url='/Rxizm32rm3CPpyyW_yanzheng_ip.php?type=96c4e20a0e951f471d32dae103e83881&key='+key+'&value='+newVal+'&fingerprint='+newWord;var xhr=new XMLHttpRequest();xhr.open('post',url);xhr.onreadystatechange=function(){if(xhr.readyState===4&&xhr.status===200){setTimeout(function(){location.reload()},3000)}};xhr.send()};
        </script>
    </body>
</html>]],ngx.md5(ip),os.time(),ngx.md5(ip),ngx.md5(user_agent))

    return jsbody
    
end 


function body_btwaf()
  if not config['open']  then return false end
  if not check_type() then return false end 
  
  server_name2=get_server_name_waf()
  server_name = string.gsub(server_name2,'_','.')
     
  local get_body=get_body_character_string()
  local site_body=get_site_character_string(site_config[server_name])
  if  site_config and site_config[server_name]~=nil and site_config[server_name]['cc']~=nil and site_config[server_name]['cc']['cc_increase_type']=='browser' then
      if ngx.status~=200 then  return false end  
      --if cc_increase_static() then return false end
      if white_rule==false  and  site_config[server_name] then 
            local get_headers=ngx.req.get_headers(100)
            local ip =body_get_client_ip(get_headers)
        	if get_headers['user-agent']==nil then
        	  get_headers['user-agent']="Windows"
        	end
        	token2=ngx.md5(ip..get_headers['user-agent']..server_name.."browser"..server_name)
        	if not ngx.shared.btwaf:get(token2) then 
                local chunk= ngx.arg[1]
                if chunk then 
                    local chunks=""
                    if #chunk<100 then 
                          chunks=chunk
                    else
                        chunks =string.sub(chunk,1,100)
                    end 
                    if ngx.re.find(chunks,[[<!Doctype html>]],'ijo')  then
                        if ngx.var.uri=="/Rxizm32rm3CPpyyW_yanzheng_ip.php" then return false end 
                    	token=ngx.md5(ip..get_headers['user-agent']..server_name.."browser"..today)
                    	cac_token=ngx.shared.btwaf:get(token)
                    	if not cac_token or cac_token==nil then 
                    	    ngx.arg[1]=get_html(ip,get_headers['user-agent'],server_name,os.date("%Y-%m-%d"))..ngx.arg[1]
                    	    return false
                    	end 
                          local yanzheng_ipdata=ngx.md5(ip..get_headers['user-agent'])
                          if ngx.shared.btwaf_data:get(cac_token) then 
                              if ngx.shared.btwaf_data:get(cac_token) ~=yanzheng_ipdata then 
                                  ngx.shared.btwaf_data:delete(cac_token)
                                  ngx.shared.btwaf:delete(token)
                    	            ngx.arg[1]=get_html(ip,get_headers['user-agent'],server_name,os.date("%Y-%m-%d"))..ngx.arg[1]
                                  return false
                              end 
                          end
                            cookie_list=getcookie(get_headers)
                        	if cookie_list[token] then 
                        	    for i,k in pairs(cookie_list[token]) do 
                        	       if k==cac_token then
                        	           return false
                        	       end
                        	    end
                        	end
                    	    ngx.arg[1]=get_html(ip,get_headers['user-agent'],server_name,os.date("%Y-%m-%d"))..ngx.arg[1]
                        	return false
                    end
                end
            end 
        end 
    else 
      if not get_body and not site_body then return false end 
      local chunk, eof = ngx.arg[1], ngx.arg[2]
      local buffered = ngx.ctx.buffered
      if not buffered then
            buffered = {}
            ngx.ctx.buffered = buffered
      end
      if chunk ~= "" then
          buffered[#buffered + 1] = chunk
          ngx.arg[1] = nil
      end
      if eof then
          local whole = table.concat(buffered)
          ngx.ctx.buffered = nil
          if get_body then
              for __,v in pairs(get_body)
              do 
                  for k2,v2 in pairs(v)
                      do
                          if type(k2)=='string' then
									if #v2 >#k2 then 
										v2 =string.sub(v2, 0, #k2)
									end 
									if #v2 <#k2 then 
										v3 =string.sub('                                                                                           ', 0,  #k2-#v2)
										v2=v2..v3
								   end 
                                  whole,c1 = string.gsub(whole,k2,v2)
                                  --if c1 > 0 then ngx.header.content_length = nil end
                          end
                     end
              end
          end
          if waf_site_config then 
            if site_body then
                for __,v in pairs(site_body)
                do 
                      for k2,v2 in pairs(v)
                        do
                            if type(k2)=='string' then
									if #v2 >#k2 then 
										v2 =string.sub(v2, 0, #k2)
									end 
									if #v2 <#k2 then 
										v3 =string.sub('                                                                                           ', 0,  #k2-#v2)
										v2=v2..v3
								   end 
                                ngx.header.content_length = nil
                                whole,c2 = string.gsub(whole,k2,v2)
                                --if c2 > 0 then ngx.header.content_length = nil end
                            end
                        end
                end
            end
        end
      ngx.arg[1] = whole
      end
    end 
end
local ok,_ = pcall(function()
	return body_btwaf()
end)