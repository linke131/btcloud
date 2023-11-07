#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/boot

# 安装
Install_Boot()
{
    echo '安装完成' > $install_tmp
}

# 卸载
Uninstall_Boot()
{
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_Boot
elif [ "${1}" == 'uninstall' ];then
	Uninstall_Boot
else
    echo 'Error'
fi
