#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn file hash check

### BEGIN INIT INFO
# Provides:          bt_hashcheck
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_hashcheck
# Description:       starts the bt_hashcheck
### END INIT INFO

panel_path=/www/server/panel/plugin/file_hash_check
init_file=$panel_path/bt_hashcheck
chmod +x $init_file
cd $panel_path
panel_start()
{        
        isStart=$(ps aux |grep bt_hashcheck|grep -v init.d|grep -v grep|awk '{print $2}'|xargs)
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-HashCheck service... \c"
                nohup "/www/server/panel/pyenv/bin/python" $init_file &> $panel_path/service.log &
                sleep 0.5
                isStart=$(ps aux |grep bt_hashcheck|grep -v init.d|grep -v grep|awk '{print $2}'|xargs)
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        cat $panel_path/service.log
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: Bt-HashCheck service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                echo "Starting  Bt-HashCheck service (pid $isStart) already running"
        fi
}

panel_stop()
{
	echo -e "Stopping Bt-HashCheck service... \c";
        pids=$(ps aux |grep bt_hashcheck|grep -v grep|grep -v init.d|awk '{print $2}'|xargs)
        arr=($pids)

        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "\033[32mdone\033[0m"
}

panel_status()
{
        isStart=$(ps aux |grep bt_hashcheck|grep -v grep|grep -v init.d|awk '{print $2}'|xargs)
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-HashCheck service (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt-HashCheck service not running\033[0m"
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
                echo "Usage: /etc/init.d/bt_hashcheck {start|stop|restart|reload}"
        ;;
esac