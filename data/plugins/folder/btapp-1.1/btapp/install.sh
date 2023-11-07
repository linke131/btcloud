#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/btapp

Install_btapp()
{
	echo 'Successify'
}


Uninstall_btapp()
{
	rm -rf /www/server/panel/static/btapp
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_btapp
elif [ "${1}" == 'uninstall' ];then
	Uninstall_btapp
fi
