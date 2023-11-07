#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
plugin_path=/www/server/panel/plugin/node_admin
Install_node_admin()
{
	echo '安装完成' > $install_tmp
}

Uninstall_node_admin()
{
	rm -rf $plugin_path
}


action=$1
if [ "${1}" == 'install' ];then
	Install_node_admin
elif [ "${1}" == 'update' ];then
	Install_node_admin
else
	Uninstall_node_admin
fi
