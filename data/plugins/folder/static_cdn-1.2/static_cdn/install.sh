#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/static_cdn

# 安装
Install_static_cdn()
{

	mkdir -p $pluginPath
	mkdir -p $pluginPath/log
	mkdir -p $pluginPath/profile
	echo '正在安装脚本文件...' > $install_tmp
	\cp -a -r $pluginPath/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-static_cdn.png
	echo '安装完成' > $install_tmp
}

# 卸载
Uninstall_static_cdn()
{
    rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_static_cdn
elif [ "${1}" == 'uninstall' ];then
	Uninstall_static_cdn
else
    echo 'Error'
fi

