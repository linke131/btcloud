#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_linuxsys()
{
	echo 'Successify'
}

Uninstall_linuxsys()
{
	rm -rf /www/server/panel/plugin/linuxsys
}


action=$1
if [ "${1}" == 'install' ];then
	Install_linuxsys
else
	Uninstall_linuxsys
fi
