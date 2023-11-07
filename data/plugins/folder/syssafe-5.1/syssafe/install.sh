#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/syssafe
python_bin='python'
if [ -f /www/server/panel/pyenv/bin/python ];then
    python_bin='/www/server/panel/pyenv/bin/python'
fi


Install_syssafe()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/sites
	initSh=/etc/init.d/bt_syssafe
	\cp -f $pluginPath/init.sh $initSh
	chmod +x $initSh
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_syssafe defaults
	else
		chkconfig --add bt_syssafe
		chkconfig --level 2345 bt_syssafe on
	fi
	$initSh stop
	$initSh start
	chmod -R 600 $pluginPath

	which systemctl
	if [ $? ];then
		systemctl daemon-reload
	fi
	echo 'Successify'
}

Uninstall_syssafe()
{
	initSh=/etc/init.d/bt_syssafe
	$initSh stop
	chkconfig --del bt_syssafe
	$python_bin $pluginPath/stop.py
	$python_bin $pluginPath/syssafe_pub.py 2
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_syssafe
else
	Uninstall_syssafe
fi
