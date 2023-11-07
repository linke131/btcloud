#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'


Get_Pack_Manager(){
	if [ -f "/usr/bin/yum" ] && [ -d "/etc/yum.repos.d" ]; then
		PM="yum"
	elif [ -f "/usr/bin/apt-get" ] && [ -f "/usr/bin/dpkg" ]; then
		PM="apt-get"		
	fi
}

Service_Add(){
	Get_Pack_Manager
	if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ]; then
		chkconfig --add btnotice
		chkconfig --level 2345 btnotice on
		Centos9Check=$(cat /etc/redhat-release |grep ' 9')
		if [ "${Centos9Check}" ];then
            cp -a -r /www/server/panel/plugin/security_notice/btnotice.service /usr/lib/systemd/system/btnotice.service 
			chmod +x /usr/lib/systemd/system/btnotice.service 
			systemctl enable btnotice
		fi		
	elif [ "${PM}" == "apt-get" ]; then
		update-rc.d btnotice defaults
	fi 
}


restart() {
    status=$`/etc/init.d/btnotice status`
    if [[ $status == *"already running"* ]]; then
        /etc/init.d/btnotice restart
    fi
}

Install_webhook()
{	
	chmod +x /www/server/panel/plugin/security_notice/btnotice.sh
	\cp -a -r /www/server/panel/plugin/security_notice/btnotice.sh  /etc/init.d/btnotice
	chmod +x /etc/init.d/btnotice
	chmod +x /www/server/panel/plugin/security_notice/webshell_scan
	if [ -f "/etc/init.d/btnotice" ]; then
		Service_Add
		mkdir  /www/server/panel/plugin/security_notice/Recycle_bin
		\cp -a -r /www/server/panel/plugin/security_notice/ico-security_notice.png /www/server/panel/BTPanel/static/img/soft_ico/ico-security_notice.png
		#检测进程是否存在。如果存在的话。则重启一下进程
		restart
		
		echo '安装完成' > $install_tmp
	else
		echo '安装失败,可能安装了系统加固' > $install_tmp
	fi 
}

Uninstall_webhook()
{
	rm -rf /www/server/panel/plugin/security_notice/info.json
	rm -rf /www/server/panel/plugin/security_notice/logs
	rm -rf /www/server/panel/plugin/security_notice/modules
	rm -rf /www/server/panel/plugin/security_notice/*.py
	rm -rf /www/server/panel/plugin/security_notice/BT-Notice
	rm -rf /www/server/panel/plugin/security_notice/*.sh
}

action=$1
if [ "${1}" == 'install' ];then
	Install_webhook
else
	Uninstall_webhook
fi
