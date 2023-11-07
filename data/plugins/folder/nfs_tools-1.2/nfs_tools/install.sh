#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/nfs_tools
initSh=/etc/init.d/bt_nfs_mount

Install_nfs_tools()
{
	mkdir -p $pluginPath/config
	install_nfs_server
	\cp -a -r $pluginPath/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-nfs_tools.png
	\cp -f $pluginPath/init.sh $initSh

	
	chmod +x $initSh

	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_nfs_mount defaults
	else
		chkconfig --add bt_nfs_mount
		chkconfig --level 2345 bt_nfs_mount on
	fi
	
	$initSh stop
	$initSh start

	
	chmod -R 600 $pluginPath
	echo > /www/server/panel/data/reload.pl
	echo 'Successify'
}

Uninstall_nfs_tools()
{
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_syssafe remove
	else
		chkconfig --del bt_syssafe
	fi
	rm -f $initSh
	rm -rf $pluginPath
	echo 'Successify'
}


install_nfs_server(){
	if [ -f /usr/bin/apt ];then
		apt install nfs-kernel-server -y
	else
		yum install nfs-utils -y
	fi

	if [ ! -f /usr/sbin/nfsstat ];then
		echo 'Error: nfs-server服务未能成功安装，请检查yun/apt安装器是否正常!'
		exit;
	fi

	systemctl enable nfs-server
	systemctl start nfs-server
	systemctl enable rpcbind
	systemctl start rpcbind
}


action=$1
if [ "${action}" == 'install' ];then
	Install_nfs_tools
elif [ "${action}" == 'uninstall' ];then
	Uninstall_nfs_tools
fi
