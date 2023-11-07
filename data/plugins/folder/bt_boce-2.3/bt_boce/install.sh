#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath='/www/server/panel/plugin/bt_boce/'
Install_logs()
{
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	if [  -f /www/server/panel/BTPanel/static/img/soft_ico/ico-bt_boce.png ];then
		rm -rf /www/server/panel/BTPanel/static/img/soft_ico/ico-bt_boce.png 
	fi
	cp -p $pluginPath/ico-bt_boce.png  /www/server/panel/BTPanel/static/img/soft_ico/
	echo '安装完成' > $install_tmp
	echo '安装完成'
}
Uninstall_logs()
{
	rm -rf /www/server/panel/plugin/bt_boce
	echo '卸载成功'
}

action=$1
if [ "${1}" == 'install' ];then
	Install_logs
else
	Uninstall_logs
fi
