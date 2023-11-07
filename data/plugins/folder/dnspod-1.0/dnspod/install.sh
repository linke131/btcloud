#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

Install_dnspod()
{
	pip install tencentcloud-sdk-python
	btpip install tencentcloud-sdk-python
	echo '安装完成' > $install_tmp
}

Uninstall_dnspod()
{
	rm -rf /www/server/panel/plugin/dnspod
}


action=$1
if [ "${1}" == 'install' ];then
	Install_dnspod
else
	Uninstall_dnspod
fi
