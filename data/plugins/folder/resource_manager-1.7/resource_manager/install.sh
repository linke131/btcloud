#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/resource_manager
Install()
{
  if [ -f "/usr/bin/apt-get" ];then
    apt install nethogs -y
  elif [ -f "/usr/bin/yum" ];then
    yum install nethogs -y
  fi
  ps -ef | grep nethogs | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
  python $pluginPath/delete_task.py
  echo '安装完成' > $install_tmp
}

Uninstall()
{
  ps -ef | grep nethogs | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
  python $pluginPath/delete_task.py
  rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
  Install
elif  [ "${1}" == 'update' ];then
  Install
elif [ "${1}" == 'uninstall' ];then
  Uninstall
fi
