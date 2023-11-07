#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
os_bit=$(getconf LONG_BIT)
is_arm=$(uname -a|grep -E 'aarch64|arm|ARM')

if [ "$os_bit" = "32" ] || [ "$is_arm" != "" ];then
	echo "========================================="
	echo "错误: 不支持32位和ARM/AARCH64平台的系统!"
	echo "========================================="
	exit 0;
fi

pluginPath=/www/server/panel/plugin/php_filter
extFile=""
version=""


Install_php_filter()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/config
	mkdir -p $pluginPath/total

	echo > /www/server/panel/data/reload.pl
	echo 'Successify'
}


Uninstall_php_filter()
{
	rm -rf $pluginPath
}


action=$1
if [ "${1}" == 'install' ];then
	Install_php_filter
else
	Uninstall_php_filter
fi
