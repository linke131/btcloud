log_by_lua_block{
	local cpath = "/www/server/total/"
	if not package.path:find(cpath) then
		package.path = cpath .. "?.lua;" .. package.path
	end

	local logger = require "total_logger"
	if not logger.inited() then
		logger.init()
	end

	if logger.runtime_error() then
		return ngx.OK
	end
	
	return logger.run_logs()
}
