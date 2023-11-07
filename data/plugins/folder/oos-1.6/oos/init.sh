#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn BT-OOS

### BEGIN INIT INFO
# Provides:          BT-OOS
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts BT-OOS
# Description:       starts the BT-OOS
### END INIT INFO



panel_init(){
        panel_path=/www/server/panel
        pid_file=$panel_path/logs/oos.pid
        log_file=$panel_path/logs/oos.log
        bin_file=$panel_path/plugin/oos/BT-OOS
        cd $panel_path
        env_path=$panel_path/pyenv/bin/activate
        if [ -f $env_path ];then
                source $env_path
                pythonV=$panel_path/pyenv/bin/python
                chmod -R 700 $panel_path/pyenv/bin
        else
                pythonV=/usr/bin/python
        fi
        reg="^#\!$pythonV\$"
        is_sed=$(cat $bin_file|head -n 1|grep -E $reg)
        if [ "${is_sed}" = "" ];then
                sed -i "s@^#!.*@#!$pythonV@" $bin_file
        fi
        chmod 700 $bin_file
        s_file=/www/server/panel/plugin/syssafe/config.json
        if [ -f $s_file ];then
                is_exp=$(cat $s_file|grep BT-OOS)
                if [ "$is_exp" = "" ];then
                        sed -i 's/"PM2"/"PM2","BT-OOS"/' $s_file
                        /etc/init.d/bt_syssafe restart
                fi
        fi
}
panel_init

panel_start()
{       
        isStart=$(ps aux |grep -v /etc/init.d|grep -v grep|grep BT-OOS|grep -v grep|awk '{print $2}')
        if [ "$isStart" = "" ];then
                echo -e "Starting BT-OOS service... \c"
                $bin_file &> /dev/null
                sleep 0.5
                isStart=$(ps aux |grep -v /etc/init.d|grep -v grep|grep BT-OOS|grep -v grep|awk '{print $2}')
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        cat $log_file
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: BT-OOS service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                pid=$(cat $pid_file)
                echo "Starting  BT-OOS service (pid $pid) already running"
        fi
}

panel_stop()
{
	echo -e "Stopping BT-OOS service... \c";
        if [ -f $pid_file ];then
                pid=$(cat $pid_file)
                kill -9 $pid
                rm -f $pid_file
        fi
        pids=$(ps aux |grep -v /etc/init.d|grep BT-OOS|grep -v grep|grep -v PID|awk '{print $2}')
        if [ "$pids" != "" ];then
                kill -9 $pids
        fi
        echo -e "\033[32mdone\033[0m"
}

panel_status()
{
        pid=$(cat $pid_file)
        if [ "$pid" != '' ];then
                echo -e "\033[32mBT-OOS service (pid $pid) already running\033[0m"
        else
                echo -e "\033[31mBT-OOS service not running\033[0m"
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
                echo "Usage: /etc/init.d/bt-oos {start|stop|restart|reload}"
        ;;
esac