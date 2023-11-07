#!/bin/bash
# chkconfig: 2345 55 25
# description: BT-Safe Agent
target_dir=/www/server/panel/plugin/security_notice
cd $target_dir

server_start()
{
	isStart=$(ps aux |grep 'BT-Notice'|grep -v grep|awk '{print $2}')
	if [ "$isStart" == '' ];then
	  if [ -f $target_dir/check_status.pl ];then
		      $target_dir/btnotice.sh restart
		fi
	fi 
}
server_start