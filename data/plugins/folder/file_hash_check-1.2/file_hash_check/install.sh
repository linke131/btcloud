#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/file_hash_check
python_bin='python'
if [ -f /www/server/panel/pyenv/bin/python ];then
    python_bin='/www/server/panel/pyenv/bin/python'
fi

Install_file_hash_check()
{
	mkdir -p $pluginPath
	initSh=/etc/init.d/bt_hashcheck
	\cp -f $pluginPath/init.sh $initSh
	chmod +x $initSh
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_hashcheck defaults
	else
		chkconfig --add bt_hashcheck
		chkconfig --level 2345 bt_hashcheck on
	fi
	if [ ! -f $pluginPath/check_list.json ];then
		echo '[]' > $pluginPath/check_list.json
	fi
	$initSh stop
	$initSh start

	echo 'Successify'
}

Uninstall_file_hash_check()
{
	initSh=/etc/init.d/bt_hashcheck
	$initSh stop
	chkconfig --del bt_hashcheck
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_file_hash_check
elif ["${1}" == 'uninstall' ];then
	Uninstall_file_hash_check
else
    echo "Usage: {install|uninstall}"
fi
