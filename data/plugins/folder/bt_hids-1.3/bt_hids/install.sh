#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#配置插件安装目录
install_path=/www/server/panel/plugin/bt_hids
#存放数据
data_path=/www/server/panel/data/hids_data
#入侵检测进程pid文件
pid_file=/www/server/panel/data/hids_data/pid.pl

#安装
Install()
{
	
    mkdir -p $data_path
    chmod 600 $data_path
	#==================================================================
	#依赖安装开始
	#依赖安装结束
	#==================================================================
	echo '================================================'
	echo '安装完成'
}

#卸载
Uninstall()
{
	pid=$(cat /www/server/panel/data/hids_data/pid.pl)
	kill -9 $pid
	rm -rf $install_path
	rm -rf $data_path
	rmmod hids_driver
}

#操作判断
action=$1
if [ "${1}" == 'install' ];then
    Install
else
    Uninstall
fi
