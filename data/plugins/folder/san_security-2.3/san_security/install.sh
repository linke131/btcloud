#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath='/www/server/panel/plugin/san_security/'
Install_logs()
{
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	cp -p $pluginPath/ico-san_security.png  /www/server/panel/BTPanel/static/img/soft_ico/
	echo '安装完成' > $install_tmp
}

Uninstall_logs()
{
	rm -rf /www/server/panel/plugin/san_security
}

action=$1
if [ "${1}" == 'install' ];then
	Install_logs
else
	Uninstall_logs
fi
