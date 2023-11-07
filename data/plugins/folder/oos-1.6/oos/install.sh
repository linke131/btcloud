#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/oos

Install_oos()
{
	echo '正在安装脚本文件...' > $install_tmp
	initSh=/etc/init.d/BT-OOS
	cp -r -a $pluginPath/init.sh  $initSh 
	chmod +x $initSh
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d BT-OOS defaults
	else
		chkconfig --add BT-OOS
		chkconfig --level 2345 BT-OOS on
	fi
	$initSh stop
	$initSh start
	chmod -R 600 $pluginPath
	chmod 700 $pluginPath/BT-OOS
	echo '安装完成' > $install_tmp
}

Uninstall_oos()
{
	initSh=/etc/init.d/BT-OOS
	$initSh stop
	chkconfig --del BT-OOS
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_oos
else
	Uninstall_oos
fi
