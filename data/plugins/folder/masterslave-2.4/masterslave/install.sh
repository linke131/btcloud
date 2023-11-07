#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/masterslave

Install_masterslave()
{	
	mkdir -p $pluginPath
	\cp -a -r /www/server/panel/plugin/masterslave/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-masterslave.png
	echo 'Successify'
}

Uninstall_masterslave()
{
	rm -rf $pluginPath
	echo 'Successify'
}




if [ "${1}" == 'install' ];then
	Install_masterslave
elif [ "${1}" == 'uninstall' ];then
	Uninstall_masterslave
fi

