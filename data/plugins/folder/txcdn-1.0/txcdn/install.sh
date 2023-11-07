#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
Install_txcdn()
{
	pip install tencentcloud-sdk-python
	btpip install tencentcloud-sdk-python

	echo '安装完成' > $install_tmp
}

Uninstall_txcdn()
{
	rm -rf /www/server/panel/plugin/txcdn
}


action=$1
if [ "${1}" == 'install' ];then
	Install_txcdn
else
	Uninstall_txcdn
fi
