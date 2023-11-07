#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/bt_security
ftq_server=/usr/local/usranalyse
Install_ftq()
{
	
	echo "">/etc/ld.so.preload
	rm -rf $ftq_server/lib/*
	mkdir -p $pluginPath
	mkdir -p $ftq_server
	chmod -R 755 $ftq_server
	mkdir -p $ftq_server/etc
	mkdir -p $ftq_server/lib
	mkdir -p $ftq_server/logs
	chmod -R 777 $ftq_server/logs
	mkdir -p $ftq_server/logs/log
	mkdir -p $ftq_server/logs/total
	mkdir -p $ftq_server/logs/send
	echo 'total=0'> $ftq_server/logs/total/total.txt
	chmod 777 /usr/local/usranalyse/logs/total/total.txt
	echo ''> $ftq_server/logs/send/bt_security.json
	chmod  777  $ftq_server/logs/send/bt_security.json
	mkdir -p $ftq_server/sbin
	
	echo '正在安装脚本文件...' > $install_tmp
	if [  -f /www/server/panel/BTPanel/static/img/soft_ico/ico-bt_security.png ];then
		rm -rf /www/server/panel/BTPanel/static/img/soft_ico/ico-bt_security.png
	fi
	cp -p $pluginPath/ico-bt_security.png  /www/server/panel/BTPanel/static/img/soft_ico/
	
	siteJson=$pluginPath/sites.json
	if [ ! -f $siteJson ];then
		wget -O $siteJson $download_Url/install/plugin/bt_security/sites.json -T 5
	fi
	
	cp -a -r $pluginPath/ftq/usranalyse.ini $ftq_server/etc/usranalyse.ini
	cp -a -r  $pluginPath/ftq/usranalyse-enable $ftq_server/sbin/usranalyse-enable 
	cp -a -r  $pluginPath/ftq/usranalyse-disable $ftq_server/sbin/usranalyse-disable
	cp -a -r  $pluginPath/ftq/libusranalyse.la $ftq_server/lib/libusranalyse.la 
	cp -a -r  $pluginPath/ftq/libusranalyse.so.0.0.0  $ftq_server/lib/libusranalyse.so.0.0.0 
	cp -a -r  $pluginPath/ftq/libusranalyse.so.0 $ftq_server/lib/libusranalyse.so.0 
	cp -a -r $pluginPath/ftq/libusranalyse.so $ftq_server/lib/libusranalyse.so 
	
	usranso=`ls -l /usr/local/usranalyse/lib/libusranalyse.so | awk '{print $5}'`
	if [ $usranso -eq 0 ];then
		cp -a -r $pluginPath/ftq/libusranalyse.so $ftq_server/lib/libusranalyse.so
		cp -a -r $pluginPath/ftq/libusranalyse.la $ftq_server/lib/libusranalyse.la 
		cp -a -r $pluginPath/ftq/libusranalyse.so.0.0.0 $ftq_server/lib/libusranalyse.so.0.0.0
		cp -a -r $pluginPath/ftq/libusranalyse.so.0 $ftq_server/lib/libusranalyse.so.0
	fi
	
    dayjson=$pluginPath/day.json
    if [ ! -f $dayjson ];then
        current=`date "+%Y-%m-%d %H:%M:%S"`
        timeStamp=`date -d "$current" +%s` 
        currentTimeStamp=$(((timeStamp*1000+10#`date "+%N"`/1000000)/1000))
        echo '{"day":$currentTimeStamp}'> $dayjson
    fi
    
	chmod +x $ftq_server/sbin/usranalyse-enable
	chmod +x $ftq_server/sbin/usranalyse-disable
	usranso2=`ls -l /usr/local/usranalyse/lib/libusranalyse.so | awk '{print $5}'`
	if [ $usranso2 -eq 0 ];then
		echo "">/etc/ld.so.preload
	else
		$ftq_server/sbin/usranalyse-disable
		$ftq_server/sbin/usranalyse-enable
	fi
	rm -rf $pluginPath/ftq
	echo '安装完成' > $install_tmp 
}
 

Uninstall_ftq()
{
	$ftq_server/sbin/usranalyse-disable
	echo "">/etc/ld.so.preload
	rm -rf $pluginPath
	rm -rf $ftq_server
}


action=$1
if [ "${1}" == 'install' ];then
	Install_ftq
	echo > /www/server/panel/data/reload.pl

else
	Uninstall_ftq
fi
