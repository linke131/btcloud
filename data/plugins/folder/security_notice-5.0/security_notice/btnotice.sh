#!/bin/bash
# chkconfig: 2345 55 25
# description: BT-Safe Agent

### BEGIN INIT INFO
# Provides:          BT-Safe Agent
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts BT-Safe Agent
# Description:       starts the BT-Safe Agent Service
### END INIT INFO
target_dir=/www/server/panel/plugin/security_notice
cd $target_dir

if [ -d $target_dir/logs ];then
  echo ''
else
  mkdir $target_dir/logs
fi

server_start()
{
        isStart=$(ps aux |grep 'BT-Notice'|grep -v grep|awk '{print $2}')
        log_file=$target_dir/logs/logs.log
        if [ "$isStart" == '' ];then
                echo -e "Starting BT-Notice ... \c"
                chmod +x $target_dir/BT-Notice
                nohup $target_dir/BT-Notice >> $log_file 2>&1 &
                echo $! > $target_dir/security_notice.pid

                sleep 0.2
                isStart=$(ps aux |grep 'BT-Notice'|grep -v grep|awk '{print $2}')
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        tail -n 20 $log_file
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: BT-Notice service startup failed.\033[0m"
                        return;
                fi
                echo -e "       \033[32mdone\033[0m"
        else
                echo "Starting BT-Notice..  (pid $isStart) already running"
        fi
}

service_stop()
{
    echo -e "Stopping BT-Notice...\c";
    pids=$(ps aux |grep 'BT-Notice'|grep -v grep|awk '{print $2}')
    arr=($pids)
    for p in ${arr[@]}
    do
            kill -9 $p
    done
    echo -e "   \033[32mdone\033[0m"
}

service_status()
{
        isStart=$(ps aux |grep 'BT-Notice'|grep -v grep|awk '{print $2}')
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBBT-Notice  (pid $(echo $isStart)) already running\033[0m"
        else
                echo -e "\033[31mBT-Notice  not running\033[0m"
        fi
#        $target_dir/tools get_status
}

case "$1" in
        'start')
                server_start
                ;;
        'stop')
                service_stop
                ;;
        'restart')
                service_stop
                sleep 1
                server_start
                ;;
        'status')
                service_status
                ;;
        'default')
                                # echo Ñ¡ÏîÎª¿Õ
                ;;
esac