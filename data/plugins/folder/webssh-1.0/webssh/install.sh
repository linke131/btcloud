#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
Install_webssh()
{
	
	echo '安装完成' > $install_tmp
}

Uninstall_webssh()
{
	rm -rf /www/server/panel/plugin/webssh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_webssh
else
	Uninstall_webssh
fi
