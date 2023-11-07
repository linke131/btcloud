#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/tamper_proof

Install_tamper_proof()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/sites
	if [  -f /www/server/panel/pyenv/bin/python ];then
	  	/www/server/panel/pyenv/bin/pip install pyinotify
	else
	  	pip install pyinotify
	fi

	siteJson=$pluginPath/sites.json
	if [ ! -f $siteJson ];then
		wget -O $siteJson $download_Url/install/plugin/tamper_proof/sites.json -T 5
	fi
	initSh=/etc/init.d/bt_tamper_proof
	\cp -f $pluginPath/init.sh $initSh
	chmod +x /etc/init.d/bt_tamper_proof
	update-rc.d bt_tamper_proof defaults
	chkconfig --add bt_tamper_proof
	chkconfig --level 2345 bt_tamper_proof on
	check_fs
	chown -R root.root $pluginPath
    chmod -R 600 $pluginPath
	$initSh stop
	$initSh start
	rm -rf $pluginPath/sites
	echo > /www/server/panel/data/reload.pl
	echo 'Successify'
}

check_fs()
{
	is_max_user_instances=`cat /etc/sysctl.conf|grep max_user_instances`
	if [ "$is_max_user_instances" == "" ];then
		echo "fs.inotify.max_user_instances = 1024" >> /etc/sysctl.conf
		echo "1024" > /proc/sys/fs/inotify/max_user_instances
	fi
	
	is_max_user_watches=`cat /etc/sysctl.conf|grep max_user_watches`
	if [ "$is_max_user_watches" == "" ];then
		echo "fs.inotify.max_user_watches = 81920000" >> /etc/sysctl.conf
		echo "81920000" > /proc/sys/fs/inotify/max_user_watches
	fi
}

Uninstall_tamper_proof()
{
	initSh=/etc/init.d/bt_tamper_proof
	$initSh stop
	update-rc.d bt_tamper_proof remove
	chkconfig --del bt_tamper_proof
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_tamper_proof
else
	Uninstall_tamper_proof
fi
