#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn anti_spam

### BEGIN INIT INFO
# Provides:          bt_anti_spam
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_anti_spam
# Description:       starts the bt_anti_spam
### END INIT INFO
panel_path=/www/server/panel
pidfile=$panel_path/logs/panel.pid
cd $panel_path
env_path=$panel_path/pyenv/bin/activate
if [ -f $env_path ];then
        source $env_path
        pythonV=$panel_path/pyenv/bin/python
        chmod -R 700 $panel_path/pyenv/bin
else
        pythonV=/usr/bin/python
fi

panel_path=/www/server/panel/plugin/anti_spam
cd $panel_path

anti_start()
{
        isStart=`ps aux |grep anti_spam_server|grep -v grep|awk '{print $2}'`
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt anti spam service... \c"
                nohup $pythonV anti_spam_server.py > $panel_path/service.log 2>&1 &
                sleep 0.5
                isStart=`ps aux |grep anti_spam_server|grep -v grep|awk '{print $2}'`
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        cat $panel_path/service.log
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: Bt anti spam service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                echo "Starting  Bt anti spam service (pid $isStart) already running"
        fi
}

anti_stop()
{
		echo -e "Stopping Bt anti spam service... \c";
        pids=`ps aux |grep anti_spam_server|grep -v grep|awk '{print $2}'`
        arr=($pids)

        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "\033[32mdone\033[0m"
}

anti_status()
{
        isStart=`ps aux |grep anti_spam_server|grep -v grep|awk '{print $2}'`
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt anti spam service (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt anti spam service not running\033[0m"
        fi
}

case "$1" in
        'start')
                anti_start
                ;;
        'stop')
                anti_stop
                ;;
        'restart')
                anti_stop
                sleep 0.2
                anti_start
                ;;
        'status')
                anti_status
                ;;
        *)
                echo "Usage: /etc/init.d/bt_anti_spam {start|stop|restart}"
        ;;
esac
