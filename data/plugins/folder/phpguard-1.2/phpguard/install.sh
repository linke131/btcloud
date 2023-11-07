#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_phpguard()
{
	mkdir -p /www/server/panel/plugin/phpguard
	echo 'True' > /www/server/panel/data/502Task.pl
	echo 'Successify'
}

Uninstall_phpguard()
{
	rm -rf /www/server/panel/plugin/phpguard
	rm -f /www/server/panel/data/502Task.pl
}


action=$1
if [ "${1}" == 'install' ];then
	Install_phpguard
else
	Uninstall_phpguard
fi
