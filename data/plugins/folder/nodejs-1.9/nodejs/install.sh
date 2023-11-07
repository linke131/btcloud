#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/nodejs

Install_nodejs()
{
	mkdir -p $pluginPath

	echo 'Successify'
}

Uninstall_nodejs()
{
	rm -rf $pluginPath
}


action=$1
if [ "${1}" == 'install' ];then
	Install_nodejs
else
	Uninstall_nodejs
fi
