#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn ipfilter

### BEGIN INIT INFO
# Provides:          bt_ipfilter
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_ipfilter
# Description:       starts the bt_ipfilter
### END INIT INFO

run_file=/www/server/panel/script/bt-ipfilter
panel_start()
{        
        isStart=$(ps aux |grep -E "(bt-ipfilter)"|grep -v grep|grep -v "/etc/init.d/bt_ipfilter"|awk '{print $2}'|xargs)
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-ipFilter service... \c"
                nohup $run_file &> /dev/null &
                sleep 0.1
                isStart=$(ps aux |grep -E "(bt-ipfilter)"|grep -v grep|grep -v "/etc/init.d/bt_ipfilter"|awk '{print $2}'|xargs)
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        echo 'run error!'
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: Bt-ipFilter service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                echo "Starting  Bt-ipFilter service (pid $isStart) already running"
        fi
}

panel_stop()
{
	echo -e "Stopping Bt-ipFilter service... \c";
        pids=$(ps aux |grep -E "(bt-ipfilter)"|grep -v grep|grep -v "/etc/init.d/bt_ipfilter"|awk '{print $2}'|xargs)
        arr=($pids)

        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "\033[32mdone\033[0m"
}

panel_status()
{
        isStart=$(ps aux |grep -E "(bt-ipfilter)"|grep -v grep|grep -v "/etc/init.d/bt_ipfilter"|awk '{print $2}'|xargs)
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-ipFilter service (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt-ipFilter service not running\033[0m"
        fi
}

case "$1" in
        'start')
                panel_start
                ;;
        'stop')
                panel_stop
                ;;
        'restart')
                panel_stop
                sleep 0.2
                panel_start
                ;;
        'reload')
                panel_stop
                sleep 0.2
                panel_start
                ;;
        'status')
                panel_status
                ;;
        *)
                echo "Usage: /etc/init.d/bt_ipfilter {start|stop|restart|reload}"
        ;;
esac