#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
current=`date "+%Y-%m-%d %H:%M:%S"`
timeStamp=`date -d "$current" +%s`
currentTimeStamp=$((timeStamp*1000+`date "+%N"`/1000000))
Install_psync()
{
	pip install requests
	cp -a -r /www/server/panel/plugin/psync_api/ico-success.png /www/server/panel/BTPanel/static/img/ico-success.png
	cp -a -r /www/server/panel/plugin/psync_api/icon.png /www/server/panel/static/BTPanel/img/soft_ico/ico-psync_api.png
echo '安装完成' > $install_tmp
}

Uninstall_psync()
{
	rm -rf /www/server/panel/plugin/psync_api
}

action=$1
if [ "${1}" == 'install' ];then
	Install_psync
else
	Uninstall_psync
fi
