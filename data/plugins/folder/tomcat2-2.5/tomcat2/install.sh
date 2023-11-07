#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/tomcat2

Install_tomcat2()
{
	echo '安装完成' > $install_tmp
}

Uninstall_tomcat2()
{
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_tomcat2
elif  [ "${1}" == 'update' ];then
	Install_tomcat2
elif [ "${1}" == 'uninstall' ];then
	Uninstall_tomcat2
fi
