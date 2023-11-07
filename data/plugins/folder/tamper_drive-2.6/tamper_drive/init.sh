#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn tamper proof

### BEGIN INIT INFO
# Provides:          bt_tamper_drive
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_tamper_proof
# Description:       starts the bt_tamper_proof
### END INIT INFO
 
panel_path=/www/server/panel/plugin/tamper_drive/kos
cd $panel_path
panel_start()
{        
        isStart=`lsmod |grep tampercfg |grep -v grep|awk '{print $1}'`
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-Tamper proof service... \c"
					insmod tampercfg.ko
                sleep 0.5
                isStart=`ps aux |grep tampercore|grep -v grep|awk '{print $1}'`
                if [ "$isStart" == '' ];then
                    insmod tampercore.ko
                    return;
                fi
        else
                echo "Starting  Bt-Tamper proof service (pid $isStart) already running"
        fi
}

panel_stop()
{
		echo -e "Stopping Bt-Tamper proof service... \c";
        tampercore=`lsmod |grep tampercore |grep -v grep|awk '{print $1}'`
        if [ "$tampercore" != '' ];then
			rmmod tampercore
        fi
        
        tampercfg=`lsmod |grep tampercfg |grep -v grep|awk '{print $1}'`
        if [ "$tampercfg" != '' ];then
			rmmod tampercfg
        fi
}

 

case "$1" in
        'start')
                panel_start
                ;;
        'stop')
                panel_stop
                ;;
        *)
                echo "Usage: /etc/init.d/bt_tamper_drive {start|stop}"
        ;;
esac
