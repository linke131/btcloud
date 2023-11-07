#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/load_balance
Install_load_balance()
{
  mkdir -p $pluginPath/tcp_config
  mkdir -p /www/wwwlogs/load_balancing
  chown -R www:www /www/wwwlogs/load_balancing

  \cp -f $pluginPath/load_total.lua /www/server/panel/vhost/nginx/load_total.lua
  echo "lua_shared_dict load_total 10m;" > /www/server/panel/vhost/nginx/load_balance_shared.conf
  echo 'Successify'
}

Uninstall_load_balance()
{
  rm -rf /www/server/panel/plugin/load_balance
  rm -f /www/server/panel/vhost/nginx/load_balance_shared.conf
  echo > /www/server/panel/vhost/nginx/load_total.lua
  echo 'Successify'
}

action=$1
if [ "${1}" == 'install' ];then
  Install_load_balance
else
  Uninstall_load_balance
fi
