#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/load_balance

\cp -f $pluginPath/load_total.lua /www/server/panel/vhost/nginx/load_total.lua
echo "lua_shared_dict load_total 10m;" > /www/server/panel/vhost/nginx/load_balance_shared.conf
echo 'Successify'
