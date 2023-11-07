#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
pluginPath=/www/server/panel/plugin/users
Install_users()
{
	
	chmod -R 600 $pluginPath
	echo '安装完成' > $install_tmp
}

Uninstall_users()
{
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_users
else
	Uninstall_users
fi
