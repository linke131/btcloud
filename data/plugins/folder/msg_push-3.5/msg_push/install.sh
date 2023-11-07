#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/msg_push

Install_MsgPush()
{
    id=`ps aux|grep "/www/server/panel/plugin/msg_push"|grep -v "grep"|awk '{print $2}'`
    if [ "$id" ];then
	    kill -9 $id
	fi
	mkdir -p $pluginPath
	\cp -a -r /www/server/panel/plugin/msg_push/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-msg_push.png
	sed -i '/* * * * * \/bin\/sh \/www\/server\/panel\/plugin\/msg_push\/daemon.sh/d' /var/spool/cron/root
	nohup /www/server/panel/pyenv/bin/python /www/server/panel/plugin/msg_push/main &
	/usr/bin/echo '1' > /www/server/panel/plugin/msg_push/open.txt
	echo 'Successify'
}

Uninstall_MsgPush()
{
	rm -rf $pluginPath
	id=`ps aux|grep msg_push|grep -v "grep"|awk '{print $2}'`
	kill -9 $id
	/usr/bin/systemctl restart crond
	echo 'Successify'
}

if [ "${1}" == 'install' ];then
	Install_MsgPush
elif [ "${1}" == 'uninstall' ];then
	Uninstall_MsgPush
fi
