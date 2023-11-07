#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
Install_Gcloud()
{
	echo '正在安装前置组件...' > $install_tmp
if [ -d "/www/server/panel/pyenv" ];then
	sudo btpip install ndg-httpsclient
	sudo btpip install --ignore-installed --upgrade google-cloud-storage
else
	sudo pip install ndg-httpsclient
	sudo pip install --ignore-installed --upgrade google-cloud-storage
fi

	echo '正在安装脚本文件...' > $install_tmp
	grep "GOOGLE_APPLICATION_CREDENTIALS" ~/.bash_profile
	if [ "$?" -ne 0 ];then
		echo 'export GOOGLE_APPLICATION_CREDENTIALS="/www/server/panel/data/google.json"' >> ~/.bash_profile
	fi
	echo '安装完成' > $install_tmp
}

Uninstall_Gcloud()
{
	rm -rf /www/server/panel/plugin/gcloud_storage
	rm -f /www/server/panel/script/backup_gcloud.py
	pip uninstall google-cloud-storage -y
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_Gcloud
else
	Uninstall_Gcloud
fi
