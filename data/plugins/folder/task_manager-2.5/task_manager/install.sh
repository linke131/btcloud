#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_task_manager()
{
	is_install_pcap=$(/www/server/panel/pyenv/bin/python -m pcap 2>&1|grep 'No module named')
	if [ "$is_install_pcap" != "" ];then
		if [ -f /usr/bin/apt ];then
			is_install=$(apt list --installed|grep libpcap-dev)
			if [ "$is_install" = "" ];then
				apt install libpcap-dev -y
			fi
		elif [ -f /usr/bin/dnf ];then
			is_install=$(rpm -qa|grep libpcap-devel)
			if [ "$is_install" = "" ];then
				dnf install libpcap-devel -y
			fi
		elif [ -f /usr/bin/yum ];then
			is_install=$(rpm -qa|grep libpcap-devel)
			if [ "$is_install" = "" ];then
				yum install libpcap-devel -y
			fi
		fi
		/www/server/panel/pyenv/bin/pip3 install pypcap
	fi
	echo 'Successify'
}

Uninstall_task_manager()
{
	rm -rf /www/server/panel/plugin/task_manager
	echo 'Successify'
}

action=$1
if [ "${1}" == 'install' ];then
	Install_task_manager
else
	Uninstall_task_manager
fi
