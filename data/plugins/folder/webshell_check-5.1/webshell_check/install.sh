#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
Install_webhook()
{
	echo '安装完成' > $install_tmp
}

Uninstall_webhook()
{
	rm -rf /www/server/panel/plugin/webshell_check
}

action=$1
if [ "${1}" == 'install' ];then
	Install_webhook
else
	Uninstall_webhook
fi
