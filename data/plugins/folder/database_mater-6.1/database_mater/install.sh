#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath='/www/server/panel/plugin/database_mater/'
Install_logs()
{
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	echo '安装完成' > $install_tmp
	echo '安装完成'
}

Uninstall_logs()
{
	rm -rf /www/server/panel/plugin/database_mater
	echo '卸载完成'
}


action=$1
if [ "${1}" == 'install' ];then
	Install_logs
else
	Uninstall_logs
fi
