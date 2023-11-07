#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL
pluginPath=/www/server/panel/plugin/tamper_drive

$os_system
$os_type
check_os_systems()
{
	if [ -z "$os_system" ];then
		if [ ! -z `find /usr/bin -name apt-get` ];then
			tamper_version=`uname -r`
			if [[ $tamper_version =~ "generic" ]] || [[ $tamper_version =~ "server" ]];then
				os_system="ubuntu"
				ubuntu_v=$(cat /etc/issue|sed -r 's/.* ([0-9]+)\..*/\1/')
				##if [ubuntu_v -ne 20] && [ubuntu_v -ne 18];then
				##	return 1
				##fi
				return 1
			else
				os_system="debian"
				debian_v=$(cat /etc/debian_version|sed -r 's/.* ([0-9]+)\..*/\1/'|awk -F. '{print $1}')
				##if [debian_v -ne 10];then
				##	return 1
				##fi
				return 1
			fi
		elif [ ! -z `find /usr/bin -name yum` ];then
			os_system="centos"
			centos_v=$(cat /etc/redhat-release|sed -r 's/.* ([0-9]+)\..*/\1/')
			majorver=$(uname -r|awk -F. '{print $1}')
			zver=$(uname -r|awk -F. '{print $2}')
			if [ $centos_v -eq 7 ] && [ $majorver -eq 3 ] && [ $zver -eq 10 ];then
				os_type="centos7"
			elif [ $centos_v -eq 8 ] && [ $majorver -eq 4 ]  && [  $zver -eq 18 ];then
				os_type="centos8"
			else 
				return 1
			fi
			
		else
			return 1
		fi
	else
		if [ "$os_system" != "centos" ] && [ "$os_system" != "ubuntu" ]  && [ "$os_system" != "redhat" ] && [ "$os_system" != "debian" ];then
			return 1
		elif [ "$os_system" = "redhat" ];then
			os_system="centos"
		fi
	fi
	
	return 0
}

Install_tamper_proof()
{
	check_os_systems
	if [ $? -eq 0 ];then
		siteJson=$pluginPath/sites.json
		
		if [[ "$os_type" == "centos7" ]];then
			cp -r -a $pluginPath/kos/centosseven/tampercfg.ko $pluginPath/kos/tampercfg.ko 
			cp -r -a $pluginPath/kos/centosseven/tampercore.ko $pluginPath/kos/tampercore.ko 
		fi
		
		if [[ "$os_type" == "centos8" ]];then
			cp -r -a  $pluginPath/centosegiht/tampercfg.ko $pluginPath/kos/tampercfg.ko 
			cp -r -a  $pluginPath/kos/centosegiht/tampercore.ko $pluginPath/kos/tampercore.ko 
		fi
		 
		if [ "$os_system" == "ubuntu" ];then
			cp -r -a $pluginPath/kos/ubuntu/tampercfg.ko $pluginPath/kos/tampercfg.ko 
			cp -r -a  $pluginPath/kos/ubuntu/tampercore.ko $pluginPath/kos/tampercore.ko 
		fi
		
		if [ "$os_system" == "debian" ];then
			cp -r -a $pluginPath/kos/debian/tampercfg.ko $pluginPath/kos/tampercfg.ko 
			cp -r -a $pluginPath/kos/debian/tampercore.ko $pluginPath/kos/tampercore.ko 
		fi
		 
		initSh=/etc/init.d/bt_tamper_drive
		cp -r -a  $pluginPath/bt_tamper_drive $initSh
		chmod +x /etc/init.d/bt_tamper_drive
		chkconfig --add bt_tamper_drive
		chkconfig --level 2345 bt_tamper_drive on
		check_fs
		chown -R root.root $pluginPath
		chmod -R 666 $pluginPath
		$initSh stop
		$initSh start
		echo '安装完成' > $install_tmp
	else 
		echo "暂时不支持该系统安装"
	fi
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
	initSh=/etc/init.d/bt_tamper_drive
	$initSh stop
	
	chkconfig --del bt_tamper_drive
	rm -rf $pluginPath
	rm -f $initSh
	rm -rf /www/server/tamper
}


action=$1
if [ "${1}" == 'install' ];then
	Install_tamper_proof
	echo > /www/server/panel/data/reload.pl

else
	Uninstall_tamper_proof
fi
