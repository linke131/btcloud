log_by_lua_block {
    local log_path = "/www/wwwlogs/load_balancing"
    local today = os.date("%Y-%m-%d")
    local localtime = os.date("%Y-%m-%d %X")
    local c_key = today..'_'.. tostring(ngx.var.upstream_addr) .. '_load'
    local count_key = c_key .. '_count'
    local time_key = c_key .. '_time'
    local date_key = c_key .. '_date'
    local timeout_key = c_key .. '_timeout'
    local error_key = c_key .. '_err'
    local speed_key = c_key .. '_speed'
    local ip,method,request_time,upstream_connect_time,upstream_header_time,upstream_response_time
    
    function log_write_file(filename,body,mode)
    	local fp = io.open(filename,mode)
    	if fp == nil then
            return nil
        end
    	fp:write(body)
    	fp:flush()
    	fp:close()
    	return true
    end
    
    function log_read_file(filename)
    	local fp = io.open(filename,'rb')
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
    
    function log_check_dir(path)
    	local file = io.open(path, "rb")
    	if file then file:close() end
    	return file ~= nil
    end
    
    function log_create_dir(path)
    	os.execute("mkdir -p " .. path)
    end
    
    function log_split( str,reps )
        local resultStrList = {}
        string.gsub(str,'[^'..reps..']+',function(w)
            table.insert(resultStrList,w)
        end)
        return resultStrList
    end
    
    function log_debug(msg)
        ngx.log(ngx.ERR,'debug: ',tostring(msg))
    end
        
    function log_format_logline(logline)
        local log_line_str = ""
        for _,v in ipairs(logline)
        do
            local iv = "|"
            if log_line_str == '' then iv = "" end
            log_line_str = log_line_str ..iv.. v
        end
        return log_line_str
    end
    
    function log_write_logs()
        
        upstream_connect_time = ngx.var.upstream_connect_time
        upstream_header_time = ngx.var.upstream_header_time
        upstream_response_time = ngx.var.upstream_response_time
        if type(ngx.var.upstream_connect_time) == 'string' or upstream_connect_time == nil then 
            upstream_connect_time = 0
            upstream_header_time = 0
            upstream_response_time = 0
        end
        
        
        request_time = (upstream_connect_time + upstream_header_time + upstream_response_time) * 1000
    	local logline = {
        	                localtime , ip , ngx.var.site_name , ngx.req.get_method() , ngx.var.request_uri,
        	                tostring(ngx.var.upstream_addr),request_time,
        	                ngx.var.upstream_response_length,ngx.var.upstream_bytes_received,ngx.var.upstream_status,
        	                ngx.var.upstream_cache_status
    	                }
    	local path = log_path .. '/logs/' .. ngx.var.site_name
    	if not log_check_dir(path) then log_create_dir(path) end
    	log_write_file(path .. '/' .. today .. '.log',log_format_logline(logline) .. "\n",'ab')
    end
    
    function log_total()
        local raddr = string.gsub(tostring(ngx.var.upstream_addr),':','_')
        local addr_local = log_split(raddr,',')[1]
        local total_count_path = log_path .. '/total/' .. addr_local
        if not log_check_dir(total_count_path) then
            log_create_dir(total_count_path)
        end
        
        local total_count_file = total_count_path .. '/' .. today .. '.pl'
        
        
        local total_count = ngx.shared.load_total:get(count_key)
        local total_error = ngx.shared.load_total:get(error_key)
        local total_speed = ngx.shared.load_total:get(speed_key)
        if not total_count then
            total_tmp = log_read_file(total_count_file)
            if not total_tmp then 
                total_count = 0 
                total_error = 0
            else
                local sp_tmp = log_split(total_tmp,' ')
                total_count = tonumber(sp_tmp[1])
                total_error = tonumber(sp_tmp[2])
            end
        end
        
        if not total_speed then
            total_speed = 0
        end
        
        if not total_error then
            total_error = 0
        end
        
        total_count = total_count + 1
        ngx.shared.load_total:set(count_key,total_count,86400)
        local upstream_status = ngx.var.upstream_status
        if type(upstream_status) == 'string' then
           upstream_status = log_split(upstream_status,',')[1]
        end
        
        if upstream_status == 502 or upstream_status == '502' then
            total_error = total_error + 1
        end
        ngx.shared.load_total:set(error_key,total_error,86400)
        
        total_speed = total_speed + 1
        ngx.shared.load_total:set(speed_key,total_speed,50)
        
        ngx.shared.load_total:set(time_key,request_time,86400)
        ngx.shared.load_total:set(date_key,localtime,86400)
        
        if not ngx.shared.load_total:get(timeout_key) then
            local total_body = tostring(total_count) .. " " .. tostring(total_error) .. " " .. tostring(total_speed) .. " " .. tostring(request_time) .. " " .. tostring(os.time())
            log_write_file(total_count_file,total_body,'w+')
            ngx.shared.load_total:set(timeout_key,1,1)
            ngx.shared.load_total:set(speed_key,0,50)
        end
    end
    
    function log_main()
        ip = ngx.var.remote_addr
        log_write_logs()
        log_total()
    end
    
    log_main()
}