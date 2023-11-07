#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL

Install_node_admin()
{

	echo '安装完成' > $install_tmp
}

Uninstall_node_admin()
{
	rm -rf /www/server/panel/plugin/node_admin
}


action=$1
if [ "${1}" == 'install' ];then
	Install_node_admin
else
	Uninstall_node_admin
fi
