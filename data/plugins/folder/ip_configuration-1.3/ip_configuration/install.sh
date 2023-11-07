#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL

Install_ip_configuration()
{
    Pack="bridge-utils"
	if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ] ; then
		${PM} install ${Pack} -y
	elif [ "${PM}" == "apt-get" ]; then
		${PM} install ${Pack} -y
	fi
	btpip install pyyaml
    mkdir -p /www/server/panel/plugin/ip_configuration
    echo '正在安装脚本文件...' > $install_tmp
	echo '安装完成' > $install_tmp
	echo Successify
}

Uninstall_ip_configuration()
{
rm -rf /www/server/panel/plugin/ip_configuration
}


action=$1
if [ "${1}" == 'install' ];then
	Install_ip_configuration
else
	Uninstall_ip_configuration
fi
