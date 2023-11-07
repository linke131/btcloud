#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/clear
Install_clear()
{
	echo '安装完成'
}

Uninstall_clear()
{
	rm -rf $pluginPath
	echo '卸载完成'
}

if [ "${1}" == 'install' ];then
	Install_clear
elif  [ "${1}" == 'update' ];then
	Install_clear
elif [ "${1}" == 'uninstall' ];then
	Uninstall_clear
fi
