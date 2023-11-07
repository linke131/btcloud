xss_engine={}
local BLACKATTREVENT = {}
BLACKATTREVENT["onbeforeunload"] = true
BLACKATTREVENT["onblur"] = true
BLACKATTREVENT["onerror"] = true
BLACKATTREVENT["onfocus"] = true
BLACKATTREVENT["onhashchange"] = true
BLACKATTREVENT["onload"] = true
BLACKATTREVENT["onmessage"] = true
BLACKATTREVENT["onpageshow"] = true
BLACKATTREVENT["onresize"] = true
BLACKATTREVENT["onchange"] = true
BLACKATTREVENT["onforminput"] = true
BLACKATTREVENT["onselect"] = true
BLACKATTREVENT["onsubmit"] = true
BLACKATTREVENT["onkeydown"] = true
BLACKATTREVENT["onkeypress"] = true
BLACKATTREVENT["onkeyup"] = true
BLACKATTREVENT["onclick"] = true
BLACKATTREVENT["ondblclick"] = true
BLACKATTREVENT["onmousedown"] = true
BLACKATTREVENT["onmousemove"] = true
BLACKATTREVENT["onmouseout"] = true
BLACKATTREVENT["onmouseover"] = true
BLACKATTREVENT["onmouseup"] = true
BLACKATTREVENT["ontoggle"] = true
BLACKATTREVENT["onfocusout"]=true
BLACKATTREVENT["onfocusin"]=true
BLACKATTREVENT["onscroll"]=true
BLACKATTREVENT["onmouseenter"]=true
BLACKATTREVENT["onmouseleave"]=true
BLACKATTREVENT["onmousewheel"]=true
BLACKATTREVENT["oncontextmenu"]=true
BLACKATTREVENT["oncopy"]=true
BLACKATTREVENT["oninput"]=true
BLACKATTREVENT["oninput"]=true
BLACKATTREVENT["onbegin"]=true
BLACKATTREVENT["onanimationstart"]=true


local voidelements={
	area = true,
	base = true,
	col = true,
	command = true,
	embed = true,
	hr = true,
	img = true,
	input = true,
	keygen = true,
	link = true,
	meta = true,
	param = true,
	source = true,
	track = true,
	wbr = true,
	a=true,
	image=true,
	script=true,
	audio=true,
	video=true,
	object=true,
	svg=true,
	html=true,
	body=true,
	bgsound=true,
	style=true,
	frameset=true,
	applet=true,
	marquee=true,
	xml=true,
	div=true,
	button=true,
	embed=true,
	plaintext=true,
	var=true,
	input=true,
	iframe=true,
	details=true,
	select=true,
	isindex=true,
	form=true,
	textarea=true,
	bleh=true,
}

local infoi_name={}
infoi_name["p"]=1
infoi_name["font"]=1
infoi_name["br"]=1
infoi_name["h1"]=1
infoi_name["h2"]=1
infoi_name["h3"]=1
infoi_name["h4"]=1
infoi_name["h5"]=1
infoi_name["h6"]=1
infoi_name["hr"]=1
infoi_name["head"]=1
infoi_name["em"]=1
infoi_name["s"]=1
infoi_name["tr"]=1
infoi_name["th"]=1
infoi_name["ol"]=1
infoi_name["ul"]=1
infoi_name["li"]=1
infoi_name["td"]=1
infoi_name["tr"]=1



local function rine(val) -- Return (val) If it's Not Empty (non-zero-length)
	return (val and #val>0) and val
end
local function rit(a) -- Return (a) If it's Table
	return (type(a) == "table") and a
end
local noop = function() end
local esc = function(s) return string.gsub(s, "([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%" .. "%1") end
local str = tostring
local char = string.char
local opts = rit(htmlparser_opts) or {} -- needed for silent/noerr/noout/nonl directives, also needed to be defined before `require` in such case
local prn = opts.silent and noop or function(l,f,...)
	local fd = (l=="i") and "stdout" or "stderr"
	local t = (" [%s] "):format(l:upper())
	io[fd]
		:write('[HTMLParser]'..t..f:format(...)
			..(opts.nonl or "\n")
		)
end
local err = opts.noerr and noop or function(f,...) prn("e",f,...) end
local out = opts.noout and noop or function(f,...) prn("i",f,...) end
local line = debug and function(lvl) return debug.getinfo(lvl or 2).currentline end or noop
local dbg = opts.debug and function(f,...) prn("d",f:gsub("#LINE#",str(line(3))),...) end or noop
-- }}}
-- Requires {{{
local ElementNode = require"ElementNode"
--}}}
-- local HtmlParser = {}
local function parse(text,limit) -- {{{
	local opts = rine(opts) -- use top-level opts-table (the one, defined before requiring the module), if exists
		or rit(htmlparser_opts) -- or defined after requiring (but before calling `parse`)
		or {} -- fallback otherwise
	opts.looplimit = opts.looplimit or htmlparser_looplimit

	local text = ngx.unescape_uri(ngx.unescape_uri(text))
	local limit = limit or opts.looplimit or 1000
	local tpl = false
	if not opts.keep_comments then -- Strip (or not) comments {{{
		text = text:gsub("<!%-%-.-%-%->","") -- Many chances commented code will have syntax errors, that'll lead to parser failures
	end -- }}}

	local tpr={}

	if not opts.keep_danger_placeholders then -- {{{ little speedup by cost of potential parsing breakages
		-- search unused "invalid" bytes {{{
		local busy,i={},0;
		repeat -- {{{
			local cc = char(i)
			if not(text:match(cc)) then -- {{{
				if not(tpr["<"]) or not(tpr[">"]) then -- {{{
					if not(busy[i]) then -- {{{
						if not(tpr["<"]) then -- {{{
							tpr["<"] = cc;
						elseif not(tpr[">"]) then
							tpr[">"] = cc;
						end -- }}}
						busy[i] = true
						dbg("c:{%s}||cc:{%d}||tpr[c]:{%s}",str(c),cc:byte(),str(tpr[c]))
						dbg("busy[i]:{%s},i:{%d}",str(busy[i]),i)
						dbg("[FindPH]:#LINE# Success! || i=%d",i)
					else -- if !busy
						dbg("[FindPH]:#LINE# Busy! || i=%d",i)
					end -- if !busy -- }}}
					dbg("c:{%s}||cc:{%d}||tpr[c]:{%s}",c,cc:byte(),str(tpr[c]))
					dbg("%s",str(busy[i]))
				else -- if < or >
					dbg("[FindPH]:#LINE# Done!",i)
					break
				end -- if < or > -- }}}
			else -- text!match(cc)
				dbg("[FindPH]:#LINE# Text contains this byte! || i=%d",i)
			end -- text!match(cc) -- }}}
			local skip=1
			if i==31 then
				skip=96 -- ASCII
			end
			i=i+skip
		until (i==255) -- }}}
		i=nil
		--- }}}

		if not(tpr["<"]) or not(tpr[">"]) then
			err("Impossible to find at least two unused byte codes in this HTML-code. We need it to escape bracket-contained placeholders inside tags.")
			err("Consider enabling 'keep_danger_placeholders' option (to silence this error, if parser wasn't failed with current HTML-code) or manually replace few random bytes, to free up the codes.")
		else
			dbg("[FindPH]:#LINE# Found! || '<'=%d, '>'=%d",tpr["<"]:byte(),tpr[">"]:byte())
		end

--	dbg("tpr[>] || tpr[] || #busy%d")

		-- g {{{
		local function g(id,...)
			local arg={...}
			local orig=arg[id]
			arg[id]=arg[id]:gsub("(.)",tpr)
			if arg[id] ~= orig then
				tpl=true
				dbg("[g]:#LINE# orig: %s", str(orig))
				dbg("[g]:#LINE# replaced: %s",str(arg[id]))
			end
			dbg("[g]:#LINE# called, id: %s, arg[id]: %s, args { "..(("{%s}, "):rep(#arg):gsub(", $","")).." }",id,arg[id],...)
			dbg("[g]:#LINE# concat(arg): %s",table.concat(arg))
			return table.concat(arg)
		end
		-- g }}}

		-- tpl-placeholders and attributes {{{
		text=text
			:gsub(
				"(=[%s]-)".. -- only match attr.values, and not random strings between two random apostrophs
				"(%b'')",
				function(...)return g(2,...)end
			)
			:gsub(
				"(=[%s]-)".. -- same for "
				'(%b"")',
				function(...)return g(2,...)end
			) -- Escape "<"/">" inside attr.values (see issue #50)
			:gsub(
				"(<".. -- Match "<",
				(opts.tpl_skip_pattern or "[^!]").. -- with exclusion pattern (for example, to ignore comments, which aren't template placeholders, but can legally contain "<"/">" inside.
				")([^>]+)".. -- If matched, we want to escape '<'s if we meet them inside tag
				"(>)",
				function(...)return g(2,...)end
			)
			:gsub(
				"("..
				(tpr["<"] or "__FAILED__").. -- Here we search for "<", we escaped in previous gsub (and don't break things if we have no escaping replacement)
				")("..
				(opts.tpl_marker_pattern or "[^%w%s]").. -- Capture templating symbol
				")([%g%s]-)".. -- match placeholder's content
				"(%2)(>)".. -- placeholder's tail
				"([^>]*>)", -- remainings
				function(...)return g(5,...)end
			)
	end
-- 	logs(text)
	local index = 0
	local root = ElementNode:new(index, str(text))
	local node, descend, tpos, opentags = root, true, 1, {}

	while true do -- MainLoop {{{
-- 		if index == limit then -- {{{
-- 			err("Main loop reached loop limit (%d). Consider either increasing it or checking HTML-code for syntax errors", limit)
-- 			break
-- 		end -- }}}
		-- openstart/tpos Definitions {{{
		local openstart, name
		openstart, tpos, name = root._text:find(
				"<" ..        -- an uncaptured starting "<"
						"([%w-]+)" .. -- name = the first word, directly following the "<"
						"[^>]*>",     -- include, but not capture everything up to the next ">"
				tpos)
		dbg("[MainLoop]:#LINE# openstart=%s || tpos=%s || name=%s",str(openstart),str(tpos),str(name))
		-- }}}
		if not name then break end
		name=name:lower()
		-- Some more vars {{{
		index = index + 1
		local tag = ElementNode:new(index, str(name), (node or {}), descend, openstart, tpos)
		node = tag
		local tagst, apos = tag:gettext(), 1
        local tagloop
        
    	local info =[[((?<=[\'"\s/])[^\s/>][^\s/=>]*)(\s*=+\s*(\'[^\']*\'|"[^"]*"|(?![\'"])[^>\s]*))?(?:\s|/(?!>))*]]
        local header_data_check =ngx.re.gmatch(tagst,info)
        ret={}
        while true do
            if tagloop == limit then -- {{{
				break
            end
    	    local m, err = header_data_check()
          	if m then 
          	    k =m[1] or ""
          	    v =m[3] or ""
          	    k=k:lower()
          	    v=v:lower()
          	    if BLACKATTREVENT[k] then
                    if v ~="" then
                        return true
                    end
          	    end
          	     if k=="src" or k=="href" or k=="action"  and v  then
                    local tmp=string.gsub(v,'\n','')
                    tmp=string.gsub(tmp,'\r','')
                    if string.find(tmp,"javascript") and tmp~='\\"javascript:;\\"' and tmp~="javascript:;" and tmp~='"javascript:;"' then
                        return true
                   end
                end 
                if name =="script" and k=="src" and v then 
                    return true
                end
                
                if name =="iframe" and k=="srcdoc" and v  then 
                    return true
                elseif name =="iframe" and k=="src" and v then 
                    if string.find(v,"html") and string.find(v,"text") then
                        return true
                    end 
                end 
          	else
          		break
          	end 
          	tagloop = (tagloop or 0) + 1
        end
        if name=="script" then 
    		if  voidelements[tag.name:lower()]  then -- {{{
    			descend = false
    			tag:close()
    		else
    			descend = true
    			opentags[tag.name] = opentags[tag.name] or {}
    			if  infoi_name[tag.name]==nil then
    				table.insert(opentags[tag.name], tag)
    			else
    				if tag:length()>0 then
    					table.insert(opentags[tag.name], tag)
    				else
    					limit=limit+1
    				end
    			end
    		end
    		local closeend = tpos
    		local closingloop
    		while true do 
    			if closingloop == limit then
    				err("Tag closing loop reached loop limit (%d). Consider either increasing it or checking HTML-code for syntax errors", limit)
    				break
    			end
    			local closestart, closing, closename
    			closestart, closeend, closing, closename = root._text:find("[^<]*<(/?)([%w-]+)", closeend)
    			dbg("[TagCloseLoop]:#LINE# closestart=%s || closeend=%s || closing=%s || closename=%s",str(closestart),str(closeend),str(closing),str(closename))
    			if not closing or closing == "" then break end
    			tag = table.remove(opentags[closename] or {}) or tag -- kludges for the cases of closing void or non-opened tags
    			closestart = root._text:find("<", closestart)
    			dbg("[TagCloseLoop]:#LINE# closestart=%s",str(closestart))
    			tag:close(closestart, closeend + 1)
    			node = tag.parent
    			descend = true
    			closingloop = (closingloop or 0) + 1
    		end -- }}}
    		if tag:getcontent() ~="" then 
    		   if  #tag:getcontent()>=1 then 
    		       return true
    		    end 
    		end 
    	end
	end
	return false
end -- }}}

local function xss(text)
    local ok,status_is = pcall(function()
	    return parse(text)
    end)
    if not ok then
	    return false
    end
    return status_is
end

xss_engine.xss = xss

return xss_engine