#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

Install_score()
{
	echo '正在安装脚本文件...' > $install_tmp
	gcc /www/server/panel/plugin/score/testcpu.c -o /www/server/panel/plugin/score/testcpu -lpthread
	echo '安装完成' > $install_tmp
}

Uninstall_score()
{
	rm -rf /www/server/panel/plugin/score
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_score
else
	Uninstall_score
fi
