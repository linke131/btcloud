local cpath="/www/server/btwaf/"
local webshell_total="webshell_total/"
local today_H=os.date("%Y-%m-%d-%H")

local function write_file(filename,body)
	fp = io.open(filename,'w')
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end
local function read_webshell()
    local webshell_total="webshell_total/"
    if ngx.shared.btwaf_data:get(cpath..webshell_total..today_H..".json") then 
        return ngx.shared.btwaf_data:get(cpath..webshell_total..today_H..".json")
    end 
    local ok2,data=pcall(function()
              local data=read_file_body(cpath..webshell_total..today_H..".json")
                return json.decode(data)
    end )
    if ok2 then 
        ngx.shared.btwaf_data:set(cpath..webshell_total..today_H..".json",data,3600)
        return data
    else
        data={}
        ngx.shared.btwaf_data:set(cpath..webshell_total..today_H..".json",data,3600)
        write_file(cpath..webshell_total..today_H..".json",json.encode(data))
        return data
    end
end 


local function split2(input, delimiter)
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

local function count_sieze(data)
    local count=0
    if type(data)~="table" then return count end 
	for k,v in pairs(data) 
	do
	    count=count+1
	end 
	return count
end 

local function webshell_san()
    request_uri = ngx.var.request_uri
    local url_data=split2(request_uri,'?')
    if url_data[1] then 
        if ngx.re.match(url_data[1],'php$') then 
            local paths =ngx.var.document_root..url_data[1]
            if url_data[1]=="/Rxizm32rm3CPpyyW_yanzheng_ip.php" then return false end 
            if ngx.shared.btwaf_data:get(ngx.md5(paths)) then return false end 
            if url_data[1]~="index.php" then 
                local webshell_info=read_webshell()
                
                local flag =true
                if webshell_info[paths]~=nil then 
                    flag=false
                end 
                if flag then 
                    ngx.shared.btwaf_data:set(ngx.md5(paths),1,3600)
                    webshell_info[paths]=os.time()
                    ngx.shared.btwaf_data:set(cpath..webshell_total..today_H..".json",webshell_info,3600)
                    if not ngx.shared.btwaf_data:get(cpath..webshell_total..today_H..".json".."write_file") then 
                        info=count_sieze(webshell_info)
                        if info>=200 then 
                            ngx.shared.btwaf_data:delete(cpath..webshell_total..today_H..".json")
                            local data={}
                            write_file(cpath..webshell_total..today_H..".json",json.encode(data))
                        else
                             write_file(cpath..webshell_total..today_H..".json",json.encode(webshell_info))
                        end 
                        ngx.shared.btwaf_data:set(cpath..webshell_total..today_H..".json".."write_file",1,2)
                    end
                end
            end 
        end 
    end 
end 

function header_btwaf()
    if ngx.status==200 and ngx.req.get_method()=="POST" and ngx.re.find(ngx.var.request_uri,"php") then
		if config['webshell_opens'] then 
           webshell_san()
		end 
    end 
    if type(config)=='table' then
        local is_open_status=false
        if config['scan_conf']['open'] ~=nil then 
            is_open_status=config['scan_conf']['open']
        end
        --周期
        local cycle=60
        if config['scan_conf']['cycle'] ~=nil then 
            cycle=tonumber(config['scan_conf']['cycle'])
        end 
        --最大次数
        local limit=120
        if config['scan_conf']['limit'] ~=nil then 
            limit=tonumber(config['scan_conf']['limit'])
        end 
        if ngx.status==404 and is_open_status and not ngx.shared.spider:get(ip) and not ip_white() and not url_white() then
            if not ngx.shared.btwaf_data:get(ip..'_san') then
                ngx.shared.btwaf_data:set(ip..'_san',1,cycle)
            else 
                ngx.shared.btwaf_data:incr(ip..'_san',1)
            end 
            if ngx.shared.btwaf_data:get(ip..'_san') >limit then 
                lan_ip('scan','404扫描器拦截 '..cycle..'秒内 访问超过'..limit.."次不存在的页面.如需要调整请在【全局配置-常见扫描器】中修改频率")
            end 
        end
    end 
end
local ok,_ = pcall(function()
	return header_btwaf()
end)