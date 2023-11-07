#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/mysql_replicate


Install_MysqlReplicate()
{
	mkdir $pluginPath
    \cp -a -r /www/server/panel/plugin/mysql_replicate/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-mysql_replicate.png
	echo 'Successify'
}


Uninstall_MysqlReplicate()
{
	rm -rf $pluginPath
	echo 'Successify'
}

if [ "${1}" == 'install' ];then
	Install_MysqlReplicate
elif  [ "${1}" == 'update' ];then
	Install_MysqlReplicate
elif [ "${1}" == 'uninstall' ];then
	Uninstall_MysqlReplicate
fi
